"""
This module is responsible for generating resumes and cover letters using the LLM model.
"""
# app/libs/resume_and_cover_builder/resume_generator.py
from string import Template
from typing import Any
from src.libs.llm_manager import AIAdapter # Import AIAdapter
from src.libs.resume_and_cover_builder.llm.llm_generate_resume import LLMResumer
from src.libs.resume_and_cover_builder.llm.llm_generate_resume_from_job import LLMResumeJobDescription
from src.libs.resume_and_cover_builder.llm.llm_generate_cover_letter_from_job import LLMCoverLetterJobDescription
from src.utils.text_refinement import refine_html_content
from .module_loader import load_module
from .config import global_config

class ResumeGenerator:
    def __init__(self, ai_adapter: AIAdapter): # Accept AIAdapter
        self.ai_adapter = ai_adapter # Store the adapter

    def set_resume_object(self, resume_object):
         self.resume_object = resume_object


    # Add language parameter
    def _create_resume(self, gpt_answerer: Any, style_path, language: str):
        # Imposta il resume nell'oggetto gpt_answerer
        gpt_answerer.set_resume(self.resume_object)

        # Leggi il template HTML
        template = Template(global_config.html_template)

        try:
            with open(style_path, "r") as f:
                style_css = f.read()  # Correzione: chiama il metodo `read` con le parentesi
        except FileNotFoundError:
            raise ValueError(f"Il file di stile non è stato trovato nel percorso: {style_path}")
        except Exception as e:
            raise RuntimeError(f"Errore durante la lettura del file CSS: {e}")

        # Genera l'HTML del resume, passing the language
        body_html = gpt_answerer.generate_html_resume(language=language)

        # Refine the HTML content to improve text quality
        refined_html = refine_html_content(body_html)

        # Applica i contenuti al template
        return template.substitute(body=refined_html, style_css=style_css)

    # Add language parameter
    def create_resume(self, style_path, language: str = "English"):
        strings = load_module(global_config.STRINGS_MODULE_RESUME_PATH, global_config.STRINGS_MODULE_NAME)
        # Pass the model instance from the adapter
        gpt_answerer = LLMResumer(llm_client=self.ai_adapter.model, strings=strings)
        # Pass language to internal method
        return self._create_resume(gpt_answerer, style_path, language)

    # Add language parameter
    def create_resume_job_description_text(self, style_path: str, job_description_text: str, language: str = "English"):
        strings = load_module(global_config.STRINGS_MODULE_RESUME_JOB_DESCRIPTION_PATH, global_config.STRINGS_MODULE_NAME)
        # Pass the model instance from the adapter
        gpt_answerer = LLMResumeJobDescription(llm_client=self.ai_adapter.model, strings=strings)
        gpt_answerer.set_job_description_from_text(job_description_text)
        # Pass language to internal method
        return self._create_resume(gpt_answerer, style_path, language)

    # Add language parameter
    def create_cover_letter_job_description(self, style_path: str, job_description_text: str, language: str = "English"):
        strings = load_module(global_config.STRINGS_MODULE_COVER_LETTER_JOB_DESCRIPTION_PATH, global_config.STRINGS_MODULE_NAME)
        # Pass the model instance from the adapter
        gpt_answerer = LLMCoverLetterJobDescription(llm_client=self.ai_adapter.model, strings=strings)
        gpt_answerer.set_resume(self.resume_object)
        gpt_answerer.set_job_description_from_text(job_description_text)
        # Pass language to generator method
        cover_letter_html = gpt_answerer.generate_cover_letter(language=language)

        # Refine the HTML content to improve text quality
        refined_html = refine_html_content(cover_letter_html)

        template = Template(global_config.html_template)
        with open(style_path, "r") as f:
            style_css = f.read()
        return template.substitute(body=refined_html, style_css=style_css)


