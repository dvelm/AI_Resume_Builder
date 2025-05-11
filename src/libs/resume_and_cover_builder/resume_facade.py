"""
This module contains the FacadeManager class, which is responsible for managing the interaction between the user and other components of the application.
"""
# app/libs/resume_and_cover_builder/manager_facade.py
import hashlib
import inquirer
import os
from pathlib import Path

from loguru import logger

from src.libs.resume_and_cover_builder.llm.llm_job_parser import LLMParser
from src.job import Job
from src.libs.llm_manager import AIAdapter # Import AIAdapter
from src.utils.chrome_utils import HTML_to_PDF, show_loading_screen
from .config import global_config

class ResumeFacade:
    # Add language parameter
    # Modify constructor to accept ai_adapter instead of api_key
    def __init__(self, ai_adapter: AIAdapter, style_manager, resume_generator, resume_object, output_path, language: str = "English"):
        """
        Initialize the FacadeManager with the given API key, style manager, resume generator, resume object, log path, and language.
        Args:
            ai_adapter (AIAdapter): The AIAdapter instance managing the LLM client.
            style_manager (StyleManager): The StyleManager instance to manage styles.
            resume_generator (ResumeGenerator): The ResumeGenerator instance to generate resumes and cover letters.
            resume_object (str): The resume object to be used for generating resumes and cover letters.
            output_path (str): The path to the log file.
            language (str): The desired output language.
        """
        lib_directory = Path(__file__).resolve().parent
        global_config.STRINGS_MODULE_RESUME_PATH = lib_directory / "resume_prompt/strings.py"
        global_config.STRINGS_MODULE_RESUME_JOB_DESCRIPTION_PATH = lib_directory / "resume_job_description_prompt/strings.py"
        global_config.STRINGS_MODULE_COVER_LETTER_JOB_DESCRIPTION_PATH = lib_directory / "cover_letter_prompt/strings.py"
        global_config.STRINGS_MODULE_NAME = "strings"
        global_config.STYLES_DIRECTORY = lib_directory / "resume_style"
        global_config.LOG_OUTPUT_FILE_PATH = output_path
        # global_config.API_KEY = api_key # Remove direct API key storage if not needed elsewhere
        self.ai_adapter = ai_adapter # Store the adapter
        self.style_manager = style_manager
        self.resume_generator = resume_generator
        self.resume_generator.set_resume_object(resume_object)
        self.language = language # Store the language
        self.selected_style = None  # Property to store the selected style

    def set_driver(self, driver):
         self.driver = driver

    def prompt_user(self, choices: list[str], message: str) -> str:
        """
        Prompt the user with the given message and choices.
        Args:
            choices (list[str]): The list of choices to present to the user.
            message (str): The message to display to the user.
        Returns:
            str: The choice selected by the user.
        """
        questions = [
            inquirer.List('selection', message=message, choices=choices),
        ]
        return inquirer.prompt(questions)['selection']

    def prompt_for_text(self, message: str) -> str:
        """
        Prompt the user to enter text with the given message.
        Args:
            message (str): The message to display to the user.
        Returns:
            str: The text entered by the user.
        """
        questions = [
            inquirer.Text('text', message=message),
        ]
        return inquirer.prompt(questions)['text']


    def link_to_job(self, job_url):
        self.driver.get(job_url)
        self.driver.implicitly_wait(10)
        body_element = self.driver.find_element("tag name", "body")
        body_element = body_element.get_attribute("outerHTML")
        # Instantiate LLMParser with the adapter's model instance
        self.llm_job_parser = LLMParser(llm_client=self.ai_adapter.model)
        self.llm_job_parser.set_body_html(body_element)

        self.job = Job()
        self.job.role = self.llm_job_parser.extract_role()
        self.job.company = self.llm_job_parser.extract_company_name()
        self.job.description = self.llm_job_parser.extract_job_description()
        self.job.location = self.llm_job_parser.extract_location()
        self.job.link = job_url
        logger.info(f"Extracting job details from URL: {job_url}")


    def create_resume_pdf_job_tailored(self) -> tuple[bytes, str]:
        """
        Create a resume PDF using the selected style and the given job description text.
        Args:
            job_url (str): The job URL to generate the hash for.
            job_description_text (str): The job description text to include in the resume.
        Returns:
            tuple: A tuple containing the PDF content as bytes and the unique filename.
        """
        # Show loading screen first
        loading_file = show_loading_screen(self.driver, self.language)

        try:
            style_path = self.style_manager.get_style_path()
            if style_path is None:
                raise ValueError("You must choose a style before generating the PDF.")

            # Pass language to generator method
            html_resume = self.resume_generator.create_resume_job_description_text(style_path, self.job.description, self.language)

            # Generate a unique name using the job URL hash
            suggested_name = hashlib.md5(self.job.link.encode()).hexdigest()[:10]

            result = HTML_to_PDF(html_resume, self.driver, self.language)
            return result, suggested_name
        finally:
            # Clean up loading file
            try:
                if loading_file and os.path.exists(loading_file):
                    os.remove(loading_file)
            except Exception as e:
                logger.warning(f"Failed to clean up loading file: {e}")



    def create_resume_pdf(self) -> bytes:
        """
        Create a resume PDF using the selected style.
        Args:
            None
        Returns:
            bytes: The PDF content as bytes.
        """
        # Show loading screen first
        loading_file = show_loading_screen(self.driver, self.language)

        try:
            style_path = self.style_manager.get_style_path()
            if style_path is None:
                raise ValueError("You must choose a style before generating the PDF.")

            # Pass language to generator method
            html_resume = self.resume_generator.create_resume(style_path, self.language)
            result = HTML_to_PDF(html_resume, self.driver, self.language)
            return result
        finally:
            # Clean up loading file
            try:
                if loading_file and os.path.exists(loading_file):
                    os.remove(loading_file)
            except Exception as e:
                logger.warning(f"Failed to clean up loading file: {e}")

    def create_cover_letter(self) -> tuple[bytes, str]:
        """
        Create a cover letter based on the given job description text and job URL.
        Args:
            None
        Returns:
            tuple: A tuple containing the PDF content as bytes and the unique filename.
        """
        # Show loading screen first
        loading_file = show_loading_screen(self.driver, self.language)

        try:
            style_path = self.style_manager.get_style_path()
            if style_path is None:
                raise ValueError("You must choose a style before generating the PDF.")

            # Pass language to generator method
            cover_letter_html = self.resume_generator.create_cover_letter_job_description(style_path, self.job.description, self.language)

            # Generate a unique name using the job URL hash
            suggested_name = hashlib.md5(self.job.link.encode()).hexdigest()[:10]

            result = HTML_to_PDF(cover_letter_html, self.driver, self.language)
            return result, suggested_name
        finally:
            # Clean up loading file
            try:
                if loading_file and os.path.exists(loading_file):
                    os.remove(loading_file)
            except Exception as e:
                logger.warning(f"Failed to clean up loading file: {e}")

    def quit_driver(self):
        """
        Quit the browser driver.
        This should be called after all PDF operations are complete.
        """
        if hasattr(self, 'driver') and self.driver:
            self.driver.quit()
