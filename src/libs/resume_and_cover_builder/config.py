"""
This module is used to store the global configuration of the application.
"""
# app/libs/resume_and_cover_builder/config.py
from pathlib import Path
import yaml
from loguru import logger

class GlobalConfig:
    def __init__(self):
        self.STRINGS_MODULE_RESUME_PATH: Path = None
        self.STRINGS_MODULE_RESUME_JOB_DESCRIPTION_PATH: Path = None
        self.STRINGS_MODULE_COVER_LETTER_JOB_DESCRIPTION_PATH: Path = None
        self.STRINGS_MODULE_NAME: str = None
        self.STYLES_DIRECTORY: Path = None
        self.LOG_OUTPUT_FILE_PATH: Path = None
        self.API_KEY: str = None

        # Default values for options
        self.font_sizes = {
            'base': 110,
            'body': 100,
            'h1': 180,
            'h2': 150,
            'paragraph': 100,
            'contact_info': 110
        }

        self.margins = {
            'top': 0.8,
            'right': 0.8,
            'bottom': 0.8,
            'left': 0.8
        }

        self.spacing = {
            'h1_top': 0.5,
            'h2_top': 0.8,
            'content_bottom': 0.8,
            'job_title_bottom': 0.3,
            'job_description_item': 0.2
        }

        # Try to load options from options.yaml
        options_path = Path("data_folder/options.yaml")
        if options_path.is_file():
            try:
                with open(options_path, 'r') as f:
                    options = yaml.safe_load(f)

                    # Load font sizes if available
                    if 'font_sizes' in options and isinstance(options['font_sizes'], dict):
                        for key, value in options['font_sizes'].items():
                            if key in self.font_sizes:
                                self.font_sizes[key] = value
                        logger.info("Loaded font sizes from options.yaml")

                    # Load margins if available
                    if 'margins' in options and isinstance(options['margins'], dict):
                        for key, value in options['margins'].items():
                            if key in self.margins:
                                self.margins[key] = value
                        logger.info("Loaded margins from options.yaml")

                    # Load spacing if available
                    if 'spacing' in options and isinstance(options['spacing'], dict):
                        for key, value in options['spacing'].items():
                            if key in self.spacing:
                                self.spacing[key] = value
                        logger.info("Loaded spacing from options.yaml")
            except Exception as e:
                logger.error(f"Error loading options from {options_path}: {e}")

        # --- Calculate final spacing values based on options ---
        # Get user offset from options.yaml, default to 0.0 if not specified
        final_job_title_bottom_spacing_cm = self.spacing.get('job_title_bottom', 0.0)
        logger.debug(f"Using --job-title-bottom-spacing from options: {final_job_title_bottom_spacing_cm}cm (Defaulting to 0.0 if not specified)")
        # --- End spacing calculation ---

        # Generate the HTML template with the loaded options
        self.html_template = f"""
                            <!DOCTYPE html>
                            <html lang="en">
                            <head>
                                <meta charset="UTF-8">
                                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                                <title>Resume</title>
                                <!-- Preload fonts to prevent layout shifts -->
                                <link rel="preload" href="https://fonts.googleapis.com/css2?family=Barlow:wght@400;600&display=swap" as="style" />
                                <link rel="preload" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css" as="style" />
                                <!-- Load fonts -->
                                <link href="https://fonts.googleapis.com/css2?family=Barlow:wght@400;600&display=swap" rel="stylesheet" />
                                <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css" />
                                    <style>
                                        /* Global font size settings from options.yaml */
                                        :root {{
                                            --job-title-bottom-spacing: {final_job_title_bottom_spacing_cm}cm; /* Use calculated value */
                                            --job-description-item-spacing: {self.spacing.get('job_description_item', 0.2)}cm;
                                            --company-spacing: {self.spacing.get('company_spacing', 0.5)}cm;
                                        }}
                                        html {{
                                            font-size: {self.font_sizes['base']}%; /* Base font size percentage */
                                        }}
                                        body {{
                                            font-size: {self.font_sizes['body']/100}rem; /* Body text size */
                                            margin: {self.margins['top']}cm {self.margins['right']}cm {self.margins['bottom']}cm {self.margins['left']}cm; /* Page margins */
                                            padding: 0;
                                        }}
                                        h1 {{
                                            font-size: {self.font_sizes['h1']/100}rem; /* Headings size */
                                            margin-top: {self.spacing['h1_top']}cm; /* Space above the name */
                                        }}
                                        h2 {{
                                            font-size: {self.font_sizes['h2']/100}rem; /* Subheadings size */
                                            margin-top: {self.spacing['h2_top']}cm; /* Space above section headings */
                                        }}
                                        p, li, span {{
                                            font-size: {self.font_sizes['paragraph']/100}rem; /* Paragraph text size */
                                        }}
                                        .contact-info p {{
                                            font-size: {self.font_sizes['contact_info']/100}rem; /* Contact info size */
                                        }}
                                        @page {{
                                            margin: {self.margins['top']}cm {self.margins['right']}cm {self.margins['bottom']}cm {self.margins['left']}cm; /* Page margins for printing */
                                            size: A4; /* Explicitly set page size */
                                        }}
                                        /* Prevent blank pages */
                                        html, body {{
                                            height: auto !important;
                                            overflow: visible !important;
                                            margin: 0 !important;
                                            padding: 0 !important;
                                            position: static !important;
                                        }}
                                        body::before, body::after {{
                                            display: none !important;
                                            content: none !important;
                                        }}
                                        * {{
                                            page-break-inside: auto;
                                            page-break-after: avoid;
                                            page-break-before: avoid;
                                            break-inside: auto;
                                            break-after: avoid;
                                            break-before: avoid;
                                        }}
                                        *:first-child {{
                                            page-break-before: avoid !important;
                                            break-before: avoid !important;
                                            margin-top: 0 !important;
                                            padding-top: 0 !important;
                                        }}
                                        *:last-child {{
                                            page-break-after: avoid !important;
                                            break-after: avoid !important;
                                            margin-bottom: 0 !important;
                                            padding-bottom: 0 !important;
                                        }}
                                        main {{
                                            margin-bottom: {self.spacing['content_bottom']}cm; /* Space at the bottom of the content */
                                        }}
                                        /* Work Experience Section Styles */
                                        /* Reset all margins and paddings for consistent spacing */
                                        #work-experience .entry {{
                                            margin: 0 0 var(--company-spacing) 0 !important;
                                            padding: 0 !important;
                                        }}
                                        #work-experience .entry-header {{
                                            margin: 0 !important;
                                            padding: 0 !important;
                                        }}
                                        #work-experience .entry-details {{
                                            margin: 0 !important;
                                            padding: 0 !important;
                                            line-height: 1 !important;
                                            margin-bottom: var(--job-title-bottom-spacing) !important; /* Apply spacing here */
                                        }}
                                        #work-experience .entry-title {{
                                            margin: 0 !important;
                                            padding: 0 !important;
                                        }}
                                        #work-experience .compact-list {{
                                            margin: 0 !important;
                                            padding: 0 !important;
                                            padding-top: 0 !important; /* Ensure no top padding */
                                            padding-left: 20px !important; /* Add consistent left padding for bullet points */
                                            line-height: 1.2 !important;
                                            position: relative !important; /* Ensure proper positioning */
                                        }}
                                        #work-experience .compact-list li {{
                                            margin-bottom: var(--job-description-item-spacing) !important;
                                            padding: 0 !important;
                                        }}
                                        #work-experience .compact-list li:last-child {{
                                            margin-bottom: 0 !important;
                                        }}
                                        $style_css
                                    </style>
                            </head>
                            <body>
                            $body
                            </body>
                            </html>
                            """

global_config = GlobalConfig()
