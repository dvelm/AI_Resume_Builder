import base64
import os
import re
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Tuple, List

import inquirer
import yaml
from src.libs.llm_manager import AIAdapter
from src.libs.resume_and_cover_builder import ResumeFacade, ResumeGenerator, StyleManager
from src.resume_schemas.resume import Resume
from src.logging import logger
from src.utils.chrome_utils import init_browser
from src.utils.constants import (
    PLAIN_TEXT_RESUME_YAML,
    SECRETS_YAML,
    WORK_PREFERENCES_YAML,
)
from src.job_application_manager import JobApplicationManager
from src.job_boards.job_board_factory import JobBoardFactory
from src.job_application_tracker import JobApplicationTracker
from src.utils.ui_translations import get_ui_string, UI_STRINGS
from src.utils.loading_screen import show_loading_screen
# AI Resume Builder imports


class ConfigError(Exception):
    """Custom exception for configuration-related errors."""
    pass


class ConfigValidator:
    """Validates configuration and secrets YAML files."""

    EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    REQUIRED_CONFIG_KEYS = {
        "remote": bool,
        "experience_level": dict,
        "job_types": dict,
        "date": dict,
        "positions": list,
        "locations": list,
        "location_blacklist": list,
        "distance": int,
        "company_blacklist": list,
        "title_blacklist": list,
    }
    EXPERIENCE_LEVELS = [
        "internship",
        "entry",
        "associate",
        "mid_senior_level",
        "director",
        "executive",
    ]
    JOB_TYPES = [
        "full_time",
        "contract",
        "part_time",
        "temporary",
        "internship",
        "other",
        "volunteer",
    ]
    DATE_FILTERS = ["all_time", "month", "week", "24_hours"]
    APPROVED_DISTANCES = {0, 5, 10, 25, 50, 100}

    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate the format of an email address."""
        return bool(ConfigValidator.EMAIL_REGEX.match(email))

    @staticmethod
    def load_yaml(yaml_path: Path) -> dict:
        """Load and parse a YAML file."""
        try:
            with open(yaml_path, "r") as stream:
                return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            raise ConfigError(f"Error reading YAML file {yaml_path}: {exc}")
        except FileNotFoundError:
            raise ConfigError(f"YAML file not found: {yaml_path}")

    @classmethod
    def validate_config(cls, config_yaml_path: Path) -> dict:
        """Validate the main configuration YAML file."""
        parameters = cls.load_yaml(config_yaml_path)
        # Check for required keys and their types
        for key, expected_type in cls.REQUIRED_CONFIG_KEYS.items():
            if key not in parameters:
                if key in ["company_blacklist", "title_blacklist", "location_blacklist"]:
                    parameters[key] = []
                else:
                    raise ConfigError(f"Missing required key '{key}' in {config_yaml_path}")
            elif not isinstance(parameters[key], expected_type):
                if key in ["company_blacklist", "title_blacklist", "location_blacklist"] and parameters[key] is None:
                    parameters[key] = []
                else:
                    raise ConfigError(
                        f"Invalid type for key '{key}' in {config_yaml_path}. Expected {expected_type.__name__}."
                    )
        cls._validate_experience_levels(parameters["experience_level"], config_yaml_path)
        cls._validate_job_types(parameters["job_types"], config_yaml_path)
        cls._validate_date_filters(parameters["date"], config_yaml_path)
        cls._validate_list_of_strings(parameters, ["positions", "locations"], config_yaml_path)
        cls._validate_distance(parameters["distance"], config_yaml_path)
        cls._validate_blacklists(parameters, config_yaml_path)
        return parameters

    @classmethod
    def _validate_experience_levels(cls, experience_levels: dict, config_path: Path):
        """Ensure experience levels are booleans."""
        for level in cls.EXPERIENCE_LEVELS:
            if not isinstance(experience_levels.get(level), bool):
                raise ConfigError(
                    f"Experience level '{level}' must be a boolean in {config_path}"
                )

    @classmethod
    def _validate_job_types(cls, job_types: dict, config_path: Path):
        """Ensure job types are booleans."""
        for job_type in cls.JOB_TYPES:
            if not isinstance(job_types.get(job_type), bool):
                raise ConfigError(
                    f"Job type '{job_type}' must be a boolean in {config_path}"
                )

    @classmethod
    def _validate_date_filters(cls, date_filters: dict, config_path: Path):
        """Ensure date filters are booleans."""
        for date_filter in cls.DATE_FILTERS:
            if not isinstance(date_filters.get(date_filter), bool):
                raise ConfigError(
                    f"Date filter '{date_filter}' must be a boolean in {config_path}"
                )

    @classmethod
    def _validate_list_of_strings(cls, parameters: dict, keys: list, config_path: Path):
        """Ensure specified keys are lists of strings."""
        for key in keys:
            if not all(isinstance(item, str) for item in parameters[key]):
                raise ConfigError(
                    f"'{key}' must be a list of strings in {config_path}"
                )

    @classmethod
    def _validate_distance(cls, distance: int, config_path: Path):
        """Validate the distance value."""
        if distance not in cls.APPROVED_DISTANCES:
            raise ConfigError(
                f"Invalid distance value '{distance}' in {config_path}. Must be one of: {cls.APPROVED_DISTANCES}"
            )

    @classmethod
    def _validate_blacklists(cls, parameters: dict, config_path: Path):
        """Ensure blacklists are lists."""
        for blacklist in ["company_blacklist", "title_blacklist", "location_blacklist"]:
            if not isinstance(parameters.get(blacklist), list):
                raise ConfigError(
                    f"'{blacklist}' must be a list in {config_path}"
                )
            if parameters[blacklist] is None:
                parameters[blacklist] = []

    @staticmethod
    def validate_secrets(secrets_yaml_path: Path) -> str:
        """Validate the secrets YAML file and retrieve the LLM API key."""
        secrets = ConfigValidator.load_yaml(secrets_yaml_path)
        mandatory_secrets = ["llm_api_key"]

        for secret in mandatory_secrets:
            if secret not in secrets:
                raise ConfigError(f"Missing secret '{secret}' in {secrets_yaml_path}")

            if not secrets[secret]:
                raise ConfigError(f"Secret '{secret}' cannot be empty in {secrets_yaml_path}")

        return secrets["llm_api_key"]


class FileManager:
    """Handles file system operations and validations."""

    REQUIRED_FILES = [SECRETS_YAML, WORK_PREFERENCES_YAML, PLAIN_TEXT_RESUME_YAML]

    @staticmethod
    def validate_data_folder(app_data_folder: Path) -> Tuple[Path, Path, Path, Path]:
        """Validate the existence of the data folder and required files."""
        if not app_data_folder.is_dir():
            raise FileNotFoundError(f"Data folder not found: {app_data_folder}")

        missing_files = [file for file in FileManager.REQUIRED_FILES if not (app_data_folder / file).exists()]
        if missing_files:
            raise FileNotFoundError(f"Missing files in data folder: {', '.join(missing_files)}")

        output_folder = app_data_folder / "output"
        output_folder.mkdir(parents=True, exist_ok=True) # Add parents=True

        return ( # Correct indentation
            app_data_folder / SECRETS_YAML,
            app_data_folder / WORK_PREFERENCES_YAML,
            app_data_folder / PLAIN_TEXT_RESUME_YAML,
            output_folder,
        )

    @staticmethod
    def get_uploads(plain_text_resume_file: Path) -> Dict[str, Path]:
        """Convert resume file paths to a dictionary."""
        if not plain_text_resume_file.exists():
            raise FileNotFoundError(f"Plain text resume file not found: {plain_text_resume_file}")

        uploads = {"plainTextResume": plain_text_resume_file}

        return uploads


def prompt_for_style_and_language(style_manager: StyleManager, interface_language: str = "English") -> str:
    """
    Prompts user for resume style and output language.

    :param style_manager: The StyleManager instance
    :param interface_language: The language to use for the interface
    :return: The selected output language for the resume/cover letter
    """
    selected_language = "English" # Default language
    available_styles = style_manager.get_styles()

    if not available_styles:
        warning_msg = get_ui_string("no_styles_available", interface_language)
        logger.warning(warning_msg)
        print(warning_msg)
    else:
        # Present style choices to the user
        choices = style_manager.format_choices(available_styles)
        style_question = [
            inquirer.List(
                "style",
                message=get_ui_string("select_style", interface_language),
                choices=choices,
            )
        ]
        style_answer = inquirer.prompt(style_question)
        if style_answer and "style" in style_answer:
            selected_choice = style_answer["style"]
            for style_name, (file_name, author_link) in available_styles.items():
                if selected_choice.startswith(style_name):
                    style_manager.set_selected_style(style_name)
                    logger.info(f"Selected style: {style_name}")
                    break
        else:
            warning_msg = get_ui_string("no_style_selected", interface_language)
            logger.warning(warning_msg)
            print(warning_msg)

    # --- Language Prompt for Output ---
    language_question = [
        inquirer.List(
            'language',
            message=get_ui_string("select_output_language", interface_language),
            choices=['English', 'Italiano', get_ui_string("other_specify", interface_language)],
            default='English'
        )
    ]
    language_answer = inquirer.prompt(language_question)

    if language_answer and language_answer['language'] == get_ui_string("other_specify", interface_language):
        custom_language_question = [
            inquirer.Text(
                'custom_language',
                message=get_ui_string("enter_language", interface_language)
            )
        ]
        custom_language_answer = inquirer.prompt(custom_language_question)
        selected_language = custom_language_answer.get('custom_language', 'English').strip()
    elif language_answer:
        selected_language = language_answer['language']

    logger.info(f"Selected output language: {selected_language}")
    return selected_language


def create_cover_letter(parameters: dict, ai_adapter: AIAdapter, style_manager: StyleManager, language: str, interface_language: str = "English"):
    """
    Logic to create a Cover Letter.
    """
    try:
        logger.info("Generating a CV based on provided parameters.")

        # Carica il resume in testo semplice
        with open(parameters["uploads"]["plainTextResume"], "r", encoding="utf-8") as file:
            plain_text_resume = file.read()

        # Style selection is now handled in main() before calling this function
        questions = [
            inquirer.Text('job_url', message=get_ui_string("enter_job_url", interface_language))
        ]
        answers = inquirer.prompt(questions)
        job_url = answers.get('job_url')

        # Start the loading screen after getting the job URL
        loading_screen = show_loading_screen("cover_letter", interface_language)

        try:
            resume_generator = ResumeGenerator(ai_adapter) # Pass ai_adapter

            try:
                # Try to create the resume object with validation
                resume_object = Resume(plain_text_resume)
            except ValueError as ve:
                # Handle validation errors specifically
                loading_screen.stop()
                error_message = str(ve)
                logger.error(f"Resume validation error: {error_message}")
                print("\n⚠️ Error in resume data:")
                print(error_message)
                print("\nPlease edit your plain_text_resume.yaml file to fix these issues.")
                print("The file is located in the data_folder directory.")
                return
            except Exception as e:
                # Handle other errors
                loading_screen.stop()
                logger.error(f"Unexpected error creating resume: {e}")
                print(f"\n⚠️ An unexpected error occurred: {e}")
                return

            driver = init_browser()
            resume_generator.set_resume_object(resume_object)
            resume_facade = ResumeFacade(
                ai_adapter=ai_adapter, # Pass adapter instead of key
                style_manager=style_manager, # Pass the style_manager with selected style
                resume_generator=resume_generator,
                resume_object=resume_object,
                output_path=Path("data_folder/output"),
                language=language # Pass the selected language
            )
            resume_facade.set_driver(driver)
            resume_facade.link_to_job(job_url)
            result_base64, suggested_name = resume_facade.create_cover_letter()

            # Decodifica Base64 in dati binari
            try:
                pdf_data = base64.b64decode(result_base64)
            except base64.binascii.Error as e:
                logger.error("Error decoding Base64: %s", e)
                loading_screen.stop()  # Stop loading screen on error
                raise

            # Definisci il percorso della cartella di output utilizzando `suggested_name`
            output_dir = Path(parameters["outputFileDirectory"]) / suggested_name

            # Crea la cartella se non esiste
            try:
                output_dir.mkdir(parents=True, exist_ok=True)
                logger.info(f"Cartella di output creata o già esistente: {output_dir}")
            except IOError as e:
                logger.error("Error creating output directory: %s", e)
                loading_screen.stop()  # Stop loading screen on error
                raise

            output_path = output_dir / "cover_letter_tailored.pdf"
            try:
                with open(output_path, "wb") as file:
                    file.write(pdf_data)
                logger.info(f"CV salvato in: {output_path}")
                # Quit the driver after all PDF operations are complete
                resume_facade.quit_driver()
                # Stop the loading screen
                loading_screen.stop()
            except IOError as e:
                logger.error("Error writing file: %s", e)
                # Make sure to quit the driver even if there's an error
                resume_facade.quit_driver()
                # Stop the loading screen on error
                loading_screen.stop()
                raise
        except Exception as e:
            # Make sure to stop the loading screen on any error
            loading_screen.stop()
            raise
    except Exception as e:
        logger.exception(f"An error occurred while creating the CV: {e}")
        raise


def create_resume_pdf_job_tailored(parameters: dict, ai_adapter: AIAdapter, style_manager: StyleManager, language: str, interface_language: str = "English"):
    """
    Logic to create a job-tailored CV.
    """
    try:
        logger.info("Generating a CV based on provided parameters.")

        # Carica il resume in testo semplice
        with open(parameters["uploads"]["plainTextResume"], "r", encoding="utf-8") as file:
            plain_text_resume = file.read()

        # Style selection is now handled in main() before calling this function
        questions = [
            inquirer.Text('job_url', message=get_ui_string("enter_job_url", interface_language))
        ]
        answers = inquirer.prompt(questions)
        job_url = answers.get('job_url')

        # Start the loading screen after getting the job URL
        loading_screen = show_loading_screen("resume_tailored", interface_language)

        try:
            resume_generator = ResumeGenerator(ai_adapter) # Pass ai_adapter

            try:
                # Try to create the resume object with validation
                resume_object = Resume(plain_text_resume)
            except ValueError as ve:
                # Handle validation errors specifically
                loading_screen.stop()
                error_message = str(ve)
                logger.error(f"Resume validation error: {error_message}")
                print("\n⚠️ Error in resume data:")
                print(error_message)
                print("\nPlease edit your plain_text_resume.yaml file to fix these issues.")
                print("The file is located in the data_folder directory.")
                return
            except Exception as e:
                # Handle other errors
                loading_screen.stop()
                logger.error(f"Unexpected error creating resume: {e}")
                print(f"\n⚠️ An unexpected error occurred: {e}")
                return

            driver = init_browser()
            resume_generator.set_resume_object(resume_object)
            resume_facade = ResumeFacade(
                ai_adapter=ai_adapter, # Pass adapter instead of key
                style_manager=style_manager, # Pass the style_manager with selected style
                resume_generator=resume_generator,
                resume_object=resume_object,
                output_path=Path("data_folder/output"),
                language=language # Pass the selected language
            )
            resume_facade.set_driver(driver)
            resume_facade.link_to_job(job_url)
            result_base64, suggested_name = resume_facade.create_resume_pdf_job_tailored()

            # Decodifica Base64 in dati binari
            try:
                pdf_data = base64.b64decode(result_base64)
            except base64.binascii.Error as e:
                logger.error("Error decoding Base64: %s", e)
                loading_screen.stop()  # Stop loading screen on error
                raise

            # Definisci il percorso della cartella di output utilizzando `suggested_name`
            output_dir = Path(parameters["outputFileDirectory"]) / suggested_name

            # Crea la cartella se non esiste
            try:
                output_dir.mkdir(parents=True, exist_ok=True)
                logger.info(f"Cartella di output creata o già esistente: {output_dir}")
            except IOError as e:
                logger.error("Error creating output directory: %s", e)
                loading_screen.stop()  # Stop loading screen on error
                raise

            output_path = output_dir / "resume_tailored.pdf"
            try:
                with open(output_path, "wb") as file:
                    file.write(pdf_data)
                logger.info(f"CV salvato in: {output_path}")
                # Quit the driver after all PDF operations are complete
                resume_facade.quit_driver()
                # Stop the loading screen
                loading_screen.stop()
            except IOError as e:
                logger.error("Error writing file: %s", e)
                # Make sure to quit the driver even if there's an error
                resume_facade.quit_driver()
                # Stop the loading screen on error
                loading_screen.stop()
                raise
        except Exception as e:
            # Make sure to stop the loading screen on any error
            loading_screen.stop()
            raise
    except Exception as e:
        logger.exception(f"An error occurred while creating the CV: {e}")
        raise


def create_resume_pdf(parameters: dict, ai_adapter: AIAdapter, style_manager: StyleManager, language: str, interface_language: str = "English"):
    """
    Logic to create a base CV.
    """
    # Start the loading screen
    loading_screen = show_loading_screen("resume", interface_language)

    try:
        logger.info("Generating a CV based on provided parameters.")

        # Load the plain text resume
        with open(parameters["uploads"]["plainTextResume"], "r", encoding="utf-8") as file:
            plain_text_resume = file.read()

        # Style selection is now handled in main() before calling this function

        # Initialize the Resume Generator
        resume_generator = ResumeGenerator(ai_adapter) # Pass ai_adapter

        try:
            # Try to create the resume object with validation
            resume_object = Resume(plain_text_resume)
        except ValueError as ve:
            # Handle validation errors specifically
            loading_screen.stop()
            error_message = str(ve)
            logger.error(f"Resume validation error: {error_message}")
            print("\n⚠️ Error in resume data:")
            print(error_message)
            print("\nPlease edit your plain_text_resume.yaml file to fix these issues.")
            print("The file is located in the data_folder directory.")
            return
        except Exception as e:
            # Handle other errors
            loading_screen.stop()
            logger.error(f"Unexpected error creating resume: {e}")
            print(f"\n⚠️ An unexpected error occurred: {e}")
            return

        driver = init_browser()
        resume_generator.set_resume_object(resume_object)

        # Create the ResumeFacade
        resume_facade = ResumeFacade(
            ai_adapter=ai_adapter, # Pass adapter instead of key
            style_manager=style_manager, # Pass the style_manager with selected style
            resume_generator=resume_generator,
            resume_object=resume_object,
            output_path=Path("data_folder/output"),
            language=language # Pass the selected language
        )
        resume_facade.set_driver(driver)
        result_base64 = resume_facade.create_resume_pdf()

        # Decode Base64 to binary data
        try:
            pdf_data = base64.b64decode(result_base64)
        except base64.binascii.Error as e:
            logger.error("Error decoding Base64: %s", e)
            loading_screen.stop()  # Stop loading screen on error
            raise

        # Define the output directory using `suggested_name`
        output_dir = Path(parameters["outputFileDirectory"])

        # Determine unique output filename
        base_output_path = output_dir / "resume_base.pdf"
        output_path = base_output_path
        counter = 1
        while output_path.exists():
            # Check if the file might be locked by trying to open it briefly
            try:
                with open(output_path, 'ab') as test_file:
                     pass # Successfully opened (or created if it didn't exist), means not locked for writing
            except PermissionError:
                 logger.warning(f"File {output_path} seems to be locked. Trying next increment.")
                 # If locked, proceed to the next filename without trying to write here
            except Exception as lock_e:
                 logger.warning(f"Unexpected error checking file lock for {output_path}: {lock_e}. Trying next increment.")

            # Increment filename
            output_path = output_dir / f"resume_base{counter}.pdf"
            counter += 1
            if counter > 100: # Safety break to prevent infinite loops
                 logger.error("Could not find an available filename after 100 attempts.")
                 loading_screen.stop()  # Stop loading screen on error
                 raise IOError("Failed to determine a unique output filename.")


        # Write the PDF file to the determined unique path
        try:
            with open(output_path, "wb") as file:
                file.write(pdf_data)
            logger.info(f"Resume saved at: {output_path}")
            # Quit the driver after all PDF operations are complete
            resume_facade.quit_driver()
            # Stop the loading screen
            loading_screen.stop()
        except IOError as e:
            # Log specific permission error if it occurs here
            if isinstance(e, PermissionError):
                 logger.error(f"Permission denied when trying to write to {output_path}. Please check file/folder permissions and ensure the file is not open elsewhere.")
            else:
                 logger.error(f"Error writing file to {output_path}: {e}")
            # Make sure to quit the driver even if there's an error
            resume_facade.quit_driver()
            # Stop the loading screen on error
            loading_screen.stop()
            raise
    except Exception as e:
        logger.exception(f"An error occurred while creating the CV: {e}")
        # Make sure to stop the loading screen on any error
        loading_screen.stop()
        raise


def handle_inquiries(selected_actions: str, parameters: dict, ai_adapter: AIAdapter, style_manager: StyleManager, language: str, interface_language: str = "English"):
    """
    Decide which function to call based on the selected user action, style, and language.

    :param selected_actions: Action selected by the user.
    :param parameters: Configuration parameters dictionary.
    :param ai_adapter: AIAdapter instance for the language model.
    :param style_manager: StyleManager instance with selected style.
    :param language: Selected output language.
    :param interface_language: The language to use for the interface.
    """
    try:
        if not selected_actions:
             warning_msg = get_ui_string("no_actions_selected", interface_language)
             logger.warning(warning_msg)
             print(warning_msg)
             return

        # Get the translated strings for comparison
        generate_resume = get_ui_string("generate_resume", interface_language)
        generate_resume_tailored = get_ui_string("generate_resume_tailored", interface_language)
        generate_cover_letter = get_ui_string("generate_cover_letter", interface_language)
        run_automated_applications = get_ui_string("run_automated_applications", interface_language)
        view_statistics = get_ui_string("view_statistics", interface_language)
        manage_applications = get_ui_string("manage_applications", interface_language)

        if generate_resume == selected_actions:
            info_msg = get_ui_string("crafting_resume", interface_language)
            logger.info(info_msg)
            print(info_msg)
            create_resume_pdf(parameters, ai_adapter, style_manager, language, interface_language)

        elif generate_resume_tailored == selected_actions:
            logger.info("Customizing your resume to enhance your job application...")
            create_resume_pdf_job_tailored(parameters, ai_adapter, style_manager, language, interface_language)

        elif generate_cover_letter == selected_actions:
            logger.info("Designing a personalized cover letter to enhance your job application...")
            create_cover_letter(parameters, ai_adapter, style_manager, language, interface_language)

        elif run_automated_applications == selected_actions:
            logger.info("Running automated job applications...")
            run_automated_job_applications(parameters, ai_adapter, style_manager, language)

        elif view_statistics == selected_actions:
            logger.info("Viewing application statistics...")
            view_application_statistics()

        elif manage_applications == selected_actions:
            logger.info("Managing existing applications...")
            manage_existing_applications()

        else:
              logger.warning(f"Unknown action selected: {selected_actions}")

    except Exception as e:
        logger.exception(f"An error occurred while handling inquiries: {e}")
        raise

def prompt_user_action(interface_language: str = "English") -> str:
    """
    Use inquirer to ask the user which action they want to perform.

    :param interface_language: The language to use for the interface
    :return: Selected action.
    """
    try:
        # Get translated strings
        message = get_ui_string("select_action", interface_language)
        choices = [
            get_ui_string("generate_resume", interface_language),
            get_ui_string("generate_resume_tailored", interface_language),
            get_ui_string("generate_cover_letter", interface_language),
            get_ui_string("run_automated_applications", interface_language),
            get_ui_string("view_statistics", interface_language),
            get_ui_string("manage_applications", interface_language)
        ]

        questions = [
            inquirer.List(
                'action',
                message=message,
                choices=choices,
            ),
        ]
        answer = inquirer.prompt(questions)
        if answer is None:
            print("No answer provided. The user may have interrupted.")
            return ""
        return answer.get('action', "")
    except Exception as e:
        print(f"An error occurred: {e}")
        return ""


def main():
    """Main entry point for the AI Resume Builder application."""
    try:
        # Select interface language first
        interface_language_question = [
            inquirer.List(
                'interface_language',
                message="Select the interface language / Seleziona la lingua dell'interfaccia:",
                choices=['English', 'Italiano'],
                default='English'
            )
        ]
        interface_language_answer = inquirer.prompt(interface_language_question)
        interface_language = interface_language_answer.get('interface_language', 'English')

        # Define and validate the data folder
        data_folder = Path("data_folder")
        secrets_file, config_file, plain_text_resume_file, output_folder = FileManager.validate_data_folder(data_folder)

        # Validate configuration and secrets
        config = ConfigValidator.validate_config(config_file)
        llm_api_key = ConfigValidator.validate_secrets(secrets_file)

        # Instantiate the central AI Adapter
        ai_adapter = AIAdapter(config, llm_api_key)

        # Prepare parameters
        config["uploads"] = FileManager.get_uploads(plain_text_resume_file)
        config["outputFileDirectory"] = output_folder

        # Interactive prompt for user to select actions using the selected interface language
        selected_action = prompt_user_action(interface_language)

        # Prompt for style and output language if an action was selected
        selected_language = "English" # Default output language
        style_manager = StyleManager() # Initialize StyleManager
        if selected_action:
             selected_language = prompt_for_style_and_language(style_manager, interface_language)

        # Handle selected actions and execute them
        handle_inquiries(selected_action, config, ai_adapter, style_manager, selected_language, interface_language) # Pass adapter and interface language

    except ConfigError as ce:
        logger.error(f"Configuration error: {ce}")
        logger.error(
            "Refer to the configuration guide for troubleshooting: "
            "https://github.com/dvelm/AI_Resume_Builder?tab=readme-ov-file#configuration"
        )
    except FileNotFoundError as fnf:
        logger.error(f"File not found: {fnf}")
        logger.error("Ensure all required files are present in the data folder.")
    except RuntimeError as re:
        logger.error(f"Runtime error: {re}")
        logger.debug(traceback.format_exc())
    except Exception as e:
        logger.exception(f"An unexpected error occurred: {e}")


def run_automated_job_applications(parameters: dict, ai_adapter: AIAdapter, style_manager: StyleManager, language: str):
    """Run automated job applications based on work preferences"""
    try:
        # Load work preferences
        work_preferences_path = os.path.join("data_folder", WORK_PREFERENCES_YAML)
        with open(work_preferences_path, 'r') as f:
            work_preferences = yaml.safe_load(f)

        # Load resume
        plain_text_resume_path = os.path.join("data_folder", PLAIN_TEXT_RESUME_YAML)
        with open(plain_text_resume_path, "r") as f:
            plain_text_resume = f.read()

        # Initialize components
        resume_generator = ResumeGenerator(ai_adapter)

        try:
            # Try to create the resume object with validation
            resume_object = Resume(plain_text_resume)
        except ValueError as ve:
            # Handle validation errors specifically
            error_message = str(ve)
            logger.error(f"Resume validation error: {error_message}")
            print("\n⚠️ Error in resume data:")
            print(error_message)
            print("\nPlease edit your plain_text_resume.yaml file to fix these issues.")
            print("The file is located in the data_folder directory.")
            return
        except Exception as e:
            # Handle other errors
            logger.error(f"Unexpected error creating resume: {e}")
            print(f"\n⚠️ An unexpected error occurred: {e}")
            return

        resume_generator.set_resume_object(resume_object)

        # Create the ResumeFacade
        resume_facade = ResumeFacade(
            ai_adapter=ai_adapter,
            style_manager=style_manager,
            resume_generator=resume_generator,
            resume_object=resume_object,
            output_path=Path("data_folder/output"),
            language=language
        )

        # Get supported job boards
        supported_boards = JobBoardFactory.get_supported_boards()

        # Ask user which job boards to use
        questions = [
            inquirer.Checkbox(
                'job_boards',
                message="Select job boards to apply on:",
                choices=supported_boards,
                default=supported_boards[:1]  # Default to first board
            ),
            inquirer.Text(
                'max_applications',
                message="Maximum number of applications to submit (leave empty for default):",
                validate=lambda _, x: x == "" or x.isdigit()
            )
        ]
        answers = inquirer.prompt(questions)

        selected_boards = answers.get('job_boards', [])
        max_applications = int(answers.get('max_applications')) if answers.get('max_applications') else None

        if not selected_boards:
            print("No job boards selected. Aborting.")
            return

        # Create job application manager
        job_manager = JobApplicationManager(resume_facade, work_preferences)

        # Run application cycle
        results = job_manager.run_application_cycle(selected_boards, max_applications)

        # Display results
        print("\n=== Job Application Results ===")
        print(f"Applications attempted: {results['applications_attempted']}")
        print(f"Applications successful: {results['applications_successful']}")
        print(f"Applications failed: {results['applications_failed']}")
        print(f"Jobs found: {results['jobs_found']}")
        print(f"Jobs skipped: {results['jobs_skipped']}")

        if results['errors']:
            print("\nErrors encountered:")
            for error in results['errors']:
                print(f"- {error}")

    except Exception as e:
        logger.error(f"Error in automated job applications: {e}")
        print(f"An error occurred: {e}")


def view_application_statistics():
    """View statistics about job applications"""
    try:
        tracker = JobApplicationTracker()
        stats = tracker.get_application_statistics()

        print("\n=== Job Application Statistics ===")
        print(f"Total applications: {stats['total_applications']}")

        print("\nApplications by status:")
        for status, count in stats['status_counts'].items():
            print(f"  {status}: {count}")

        print("\nTop companies applied to:")
        for company, count in stats['top_companies']:
            print(f"  {company}: {count}")

        print("\nApplications by month:")
        for month, count in sorted(stats['applications_by_month'].items()):
            print(f"  {month}: {count}")

        # Show applications needing follow-up
        follow_ups = tracker.get_applications_needing_follow_up()
        if follow_ups:
            print("\nApplications needing follow-up today:")
            for app in follow_ups:
                print(f"  {app['job']['company']} - {app['job']['role']} (Applied: {app['application_date'][:10]})")

    except Exception as e:
        logger.error(f"Error viewing application statistics: {e}")
        print(f"An error occurred: {e}")


def manage_existing_applications():
    """Manage existing job applications"""
    try:
        tracker = JobApplicationTracker()
        applications = tracker.get_all_applications()

        if not applications:
            print("No applications found.")
            return

        # Create a list of application choices
        choices = [
            f"{app['job']['company']} - {app['job']['role']} ({app['status']})"
            for app in applications
        ]

        # Add a back option
        choices.append("Back to main menu")

        # Ask user which application to manage
        questions = [
            inquirer.List(
                'application',
                message="Select an application to manage:",
                choices=choices
            )
        ]
        answer = inquirer.prompt(questions)
        selected = answer.get('application')

        if selected == "Back to main menu":
            return

        # Find the selected application
        selected_index = choices.index(selected)
        app = applications[selected_index]

        # Show application details and management options
        while True:
            print(f"\n=== {app['job']['company']} - {app['job']['role']} ===")
            print(f"Status: {app['status']}")
            print(f"Applied: {app['application_date'][:10]}")
            if app.get('follow_up_date'):
                print(f"Follow-up date: {app['follow_up_date'][:10]}")

            # Show notes if any
            if app['notes']:
                print("\nNotes:")
                for note in app['notes']:
                    print(f"  {note['date'][:10]}: {note['text']}")

            # Management options
            questions = [
                inquirer.List(
                    'action',
                    message="What would you like to do?",
                    choices=[
                        "Update status",
                        "Add note",
                        "Set follow-up date",
                        "View job details",
                        "Back to application list"
                    ]
                )
            ]
            answer = inquirer.prompt(questions)
            action = answer.get('action')

            if action == "Update status":
                # Status update options
                status_options = [
                    "applied", "interview_scheduled", "interview_completed",
                    "rejected", "offer_received", "accepted", "declined"
                ]
                status_q = [
                    inquirer.List(
                        'status',
                        message="Select new status:",
                        choices=status_options
                    )
                ]
                status_answer = inquirer.prompt(status_q)
                new_status = status_answer.get('status')

                if tracker.update_status(app['id'], new_status):
                    print(f"Status updated to {new_status}")
                    # Refresh application data
                    app = tracker.get_application(app['id'])

            elif action == "Add note":
                note_q = [
                    inquirer.Text(
                        'note',
                        message="Enter note:"
                    )
                ]
                note_answer = inquirer.prompt(note_q)
                note_text = note_answer.get('note')

                if note_text and tracker.add_note(app['id'], note_text):
                    print("Note added")
                    # Refresh application data
                    app = tracker.get_application(app['id'])

            elif action == "Set follow-up date":
                # Get date input
                date_q = [
                    inquirer.Text(
                        'date',
                        message="Enter follow-up date (YYYY-MM-DD):",
                        validate=lambda _, x: bool(re.match(r'^\d{4}-\d{2}-\d{2}$', x))
                    )
                ]
                date_answer = inquirer.prompt(date_q)
                date_str = date_answer.get('date')

                try:
                    follow_up_date = datetime.strptime(date_str, "%Y-%m-%d")
                    if tracker.set_follow_up_date(app['id'], follow_up_date):
                        print(f"Follow-up date set to {date_str}")
                        # Refresh application data
                        app = tracker.get_application(app['id'])
                except ValueError:
                    print("Invalid date format. Please use YYYY-MM-DD.")

            elif action == "View job details":
                job = app['job']
                print("\n=== Job Details ===")
                print(f"Title: {job['role']}")
                print(f"Company: {job['company']}")
                print(f"Location: {job['location']}")
                print(f"Link: {job['link']}")
                if job.get('description'):
                    print("\nDescription:")
                    # Print first 300 chars of description
                    print(f"{job['description'][:300]}...")

                input("\nPress Enter to continue...")

            elif action == "Back to application list":
                break

        # Recursive call to show the application list again
        manage_existing_applications()

    except Exception as e:
        logger.error(f"Error managing applications: {e}")
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
