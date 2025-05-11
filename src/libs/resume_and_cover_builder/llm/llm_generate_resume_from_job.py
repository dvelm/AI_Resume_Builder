"""
Create a class that generates a job description based on a resume and a job description template.
"""
# app/libs/resume_and_cover_builder/llm_generate_resume_from_job.py
import os
from src.libs.resume_and_cover_builder.llm.llm_generate_resume import LLMResumer
from src.libs.resume_and_cover_builder.utils import LoggerChatModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
# from langchain_openai import ChatOpenAI # Remove if not directly used
from dotenv import load_dotenv
from loguru import logger
from pathlib import Path
from typing import Any # Import Any for type hint

# Load environment variables from .env file
load_dotenv()

log_folder = 'log/resume/gpt_resum_job_descr'
if not os.path.exists(log_folder):
    os.makedirs(log_folder)
log_path = Path(log_folder).resolve()
logger.add(log_path / "gpt_resum_job_descr.log", rotation="1 day", compression="zip", retention="7 days", level="DEBUG")

class LLMResumeJobDescription(LLMResumer):
    # Modify constructor to accept llm_client and pass it to super
    def __init__(self, llm_client: Any, strings: Any):
        super().__init__(llm_client, strings)

    def set_job_description_from_text(self, job_description_text) -> None:
        """
        Set the job description text to be used for generating the resume.
        Args:
            job_description_text (str): The plain text job description to be used.
        """
        prompt = ChatPromptTemplate.from_template(self.strings.summarize_prompt_template)
        chain = prompt | self.llm_cheap | StrOutputParser()
        output = chain.invoke({"text": job_description_text})
        self.job_description = output

    # Add language parameter
    def generate_header(self, language: str = "English") -> str:
        """
        Generate the header section of the resume, considering job description and language.
        Returns:
            str: The generated header section.
        """
        # Pass language to super() call
        return super().generate_header(language=language, data={
            "personal_information": self.resume.personal_information,
            "job_description": self.job_description
        })

    # Add language parameter
    def generate_education_section(self, language: str = "English") -> str:
        """
        Generate the education section of the resume, considering job description and language.
        Returns:
            str: The generated education section.
        """
        # Pass language to super() call
        return super().generate_education_section(language=language, data={
            "education_details": self.resume.education_details,
            "job_description": self.job_description
        })

    # Add language parameter
    def generate_work_experience_section(self, language: str = "English") -> str:
        """
        Generate the work experience section of the resume, considering job description and language.
        Returns:
            str: The generated work experience section.
        """
        # Pass language to super() call
        return super().generate_work_experience_section(language=language, data={
            "experience_details": self.resume.experience_details,
            "job_description": self.job_description
        })

    # Add language parameter
    def generate_projects_section(self, language: str = "English") -> str:
        """
        Generate the side projects section of the resume, considering job description and language.
        Returns:
            str: The generated side projects section.
        """
        # Pass language to super() call
        return super().generate_projects_section(language=language, data={
            "projects": self.resume.projects,
            "job_description": self.job_description
        })

    # Add language parameter
    def generate_achievements_section(self, language: str = "English") -> str:
        """
        Generate the achievements section of the resume, considering job description and language.
        Returns:
            str: The generated achievements section.
        """
        # Pass language to super() call
        return super().generate_achievements_section(language=language, data={
            "achievements": self.resume.achievements,
            "job_description": self.job_description
        })

    # Add language parameter
    def generate_certifications_section(self, language: str = "English") -> str:
        """
        Generate the certifications section of the resume, considering job description and language.
        Returns:
            str: The generated certifications section.
        """
        # Pass language to super() call
        return super().generate_certifications_section(language=language, data={
            "certifications": self.resume.certifications,
            "job_description": self.job_description
        })

    # Add language parameter
    def generate_additional_skills_section(self, language: str = "English") -> str:
        """
        Generate the additional skills section of the resume, considering job description and language.
        Returns:
            str: The generated additional skills section.
        """
        # Add language instruction to the prompt
        additional_skills_prompt_template = self._preprocess_template_string(
             self.strings.prompt_additional_skills + f"\n\nGenerate the response strictly in {language}."
        )
        skills = set()
        if self.resume.experience_details:
            for exp in self.resume.experience_details:
                if exp.skills_acquired:
                    skills.update(exp.skills_acquired)

        if self.resume.education_details:
            for edu in self.resume.education_details:
                if edu.exam:
                    for exam in edu.exam:
                        skills.update(exam.keys())
        prompt = ChatPromptTemplate.from_template(additional_skills_prompt_template)
        chain = prompt | self.llm_cheap | StrOutputParser()
        output = chain.invoke({
            "languages": self.resume.languages,
            "interests": self.resume.interests,
            "skills": skills,
            "job_description": self.job_description
            # "language": language # Add if needed by template
        })
        # Strip markdown fences if present
        if output.strip().startswith("```html"):
            output = output.strip()[7:] # Remove ```html
        if output.strip().endswith("```"):
            output = output.strip()[:-3] # Remove ```
        return output.strip()
