"""
UI translations for the AI Resume Builder application.
This module contains translations for all UI strings in the application.
"""

# Dictionary of UI strings in different languages
UI_STRINGS = {
    "English": {
        # Main menu
        "select_action": "Select the action you want to perform:",
        "generate_resume": "Generate Resume",
        "generate_resume_tailored": "Generate Resume Tailored for Job Description",
        "generate_cover_letter": "Generate Tailored Cover Letter for Job Description",
        "run_automated_applications": "Run Automated Job Applications (Not Available)",
        "view_statistics": "View Application Statistics (Not Available)",
        "manage_applications": "Manage Existing Applications (Not Available)",

        # Style and language selection
        "select_style": "Select a style for the resume:",
        "select_output_language": "Select the output language for the resume/cover letter:",
        "other_specify": "Other (Specify)",
        "enter_language": "Enter the desired language:",

        # Job URL prompt
        "enter_job_url": "Please enter the URL of the job description:",

        # Job board selection
        "select_job_boards": "Select job boards to apply on:",
        "max_applications": "Maximum number of applications to submit (leave empty for default):",

        # Messages
        "no_style_selected": "No style selected. Proceeding with default style.",
        "no_styles_available": "No styles available. Proceeding without style selection.",
        "generating_cv": "Generating a CV based on provided parameters.",
        "crafting_resume": "Crafting a standout professional resume...",
        "no_actions_selected": "No actions selected. Nothing to execute.",
        "no_job_boards": "No job boards selected. Aborting.",

        # Loading screen messages
        "generating_resume_loading": "Generating your professional resume...",
        "generating_tailored_resume_loading": "Creating your tailored resume for this job...",
        "generating_cover_letter_loading": "Crafting your personalized cover letter...",
        "generating_document_loading": "Preparing your document...",

        # Input prompts
        "enter_job_url": "Please enter the URL of the job description:",

        # Errors
        "config_error": "Configuration error: {error}",
        "config_guide": "Refer to the configuration guide for troubleshooting: {url}",
        "file_not_found": "File not found: {error}",
        "file_not_found_help": "Ensure all required files are present in the data folder.",

        # Language selection
        "select_interface_language": "Select the interface language:",
    },

    "Italiano": {
        # Main menu
        "select_action": "Seleziona l'azione che vuoi eseguire:",
        "generate_resume": "Genera Curriculum",
        "generate_resume_tailored": "Genera Curriculum Personalizzato per Offerta di Lavoro",
        "generate_cover_letter": "Genera Lettera di Presentazione Personalizzata",
        "run_automated_applications": "Esegui Candidature Automatiche (Non Disponibile)",
        "view_statistics": "Visualizza Statistiche Candidature (Non Disponibile)",
        "manage_applications": "Gestisci Candidature Esistenti (Non Disponibile)",

        # Style and language selection
        "select_style": "Seleziona uno stile per il curriculum:",
        "select_output_language": "Seleziona la lingua di output per il curriculum/lettera:",
        "other_specify": "Altro (Specifica)",
        "enter_language": "Inserisci la lingua desiderata:",

        # Job URL prompt
        "enter_job_url": "Inserisci l'URL dell'offerta di lavoro:",

        # Job board selection
        "select_job_boards": "Seleziona i portali di lavoro su cui candidarti:",
        "max_applications": "Numero massimo di candidature da inviare (lascia vuoto per il valore predefinito):",

        # Messages
        "no_style_selected": "Nessuno stile selezionato. Procedendo con lo stile predefinito.",
        "no_styles_available": "Nessuno stile disponibile. Procedendo senza selezione dello stile.",
        "generating_cv": "Generazione di un CV basato sui parametri forniti.",
        "crafting_resume": "Creazione di un curriculum professionale di qualità...",
        "no_actions_selected": "Nessuna azione selezionata. Niente da eseguire.",
        "no_job_boards": "Nessun portale di lavoro selezionato. Operazione annullata.",

        # Loading screen messages
        "generating_resume_loading": "Generazione del tuo curriculum professionale...",
        "generating_tailored_resume_loading": "Creazione del curriculum personalizzato per questo lavoro...",
        "generating_cover_letter_loading": "Elaborazione della tua lettera di presentazione personalizzata...",
        "generating_document_loading": "Preparazione del tuo documento...",

        # Input prompts
        "enter_job_url": "Inserisci l'URL dell'offerta di lavoro:",

        # Errors
        "config_error": "Errore di configurazione: {error}",
        "config_guide": "Consulta la guida di configurazione per la risoluzione dei problemi: {url}",
        "file_not_found": "File non trovato: {error}",
        "file_not_found_help": "Assicurati che tutti i file richiesti siano presenti nella cartella data_folder.",

        # Language selection
        "select_interface_language": "Seleziona la lingua dell'interfaccia:",
    }
}

def get_ui_string(key, language="English", **kwargs):
    """
    Get a UI string in the specified language.

    Args:
        key (str): The key of the string to get
        language (str): The language to get the string in
        **kwargs: Variables to format into the string

    Returns:
        str: The translated string
    """
    # Default to English if the language is not supported
    if language not in UI_STRINGS:
        language = "English"

    # Default to the key itself if the key is not found
    if key not in UI_STRINGS[language]:
        return key

    # Get the string and format it with the provided variables
    string = UI_STRINGS[language][key]
    if kwargs:
        try:
            return string.format(**kwargs)
        except KeyError:
            return string
    return string
