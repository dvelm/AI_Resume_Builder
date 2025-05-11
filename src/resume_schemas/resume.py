from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import yaml
import re
from pydantic import BaseModel, EmailStr, HttpUrl, Field, ValidationError



class PersonalInformation(BaseModel):
    name: Optional[str]
    surname: Optional[str]
    date_of_birth: Optional[str]
    country: Optional[str]
    city: Optional[str]
    address: Optional[str] = None # Explicitly set default to None to make it truly optional
    zip_code: Optional[str] = Field(None, min_length=5, max_length=10)
    phone_prefix: Optional[str]
    phone: Optional[str]
    email: Optional[EmailStr]
    github: Optional[HttpUrl] = None
    linkedin: Optional[HttpUrl] = None


class EducationDetails(BaseModel):
    education_level: Optional[str]
    institution: Optional[str]
    field_of_study: Optional[str]
    final_evaluation_grade: Optional[str]
    start_date: Optional[str]
    year_of_completion: Optional[int]
    location: Optional[str] = None
    country: Optional[str] = None
    # Removed exam field completely


class ExperienceDetails(BaseModel):
    position: Optional[str]
    company: Optional[str]
    employment_period: Optional[str]
    location: Optional[str]
    industry: Optional[str]
    key_responsibilities: Optional[List[Dict[str, str]]] = None
    skills_acquired: Optional[List[str]] = None


class Project(BaseModel):
    name: Optional[str]
    description: Optional[str]
    link: Optional[HttpUrl] = None


class Achievement(BaseModel):
    name: Optional[str]
    description: Optional[str]


class Certifications(BaseModel):
    name: Optional[str]
    description: Optional[str]


class Language(BaseModel):
    language: Optional[str]
    proficiency: Optional[str]


class Availability(BaseModel):
    notice_period: Optional[str]


class SalaryExpectations(BaseModel):
    salary_range_usd: Optional[str]


class SelfIdentification(BaseModel):
    gender: Optional[str]
    pronouns: Optional[str]
    veteran: Optional[str]
    disability: Optional[str]
    ethnicity: Optional[str]


class LegalAuthorization(BaseModel):
    eu_work_authorization: Optional[str]
    us_work_authorization: Optional[str]
    requires_us_visa: Optional[str]
    requires_us_sponsorship: Optional[str]
    requires_eu_visa: Optional[str]
    legally_allowed_to_work_in_eu: Optional[str]
    legally_allowed_to_work_in_us: Optional[str]
    requires_eu_sponsorship: Optional[str]


class Resume(BaseModel):
    personal_information: Optional[PersonalInformation]
    education_details: Optional[List[EducationDetails]] = None
    experience_details: Optional[List[ExperienceDetails]] = None
    projects: Optional[List[Project]] = None
    achievements: Optional[List[Achievement]] = None
    certifications: Optional[List[Certifications]] = None
    languages: Optional[List[Language]] = None
    interests: Optional[List[str]] = None

    @staticmethod
    def normalize_exam_format(exam):
        if isinstance(exam, dict):
            return [{k: v} for k, v in exam.items()]
        return exam

    def __init__(self, yaml_str: str):
        try:
            # Parse the YAML string
            data = yaml.safe_load(yaml_str)

            # Preprocess education details if present
            if 'education_details' in data and data['education_details']: # Check if list is not empty
                for ed in data['education_details']:
                    # Completely remove exam field from all education entries
                    if 'exam' in ed:
                        ed.pop('exam', None)
                    # Also remove any nested exam fields in additional_info
                    if 'additional_info' in ed and isinstance(ed['additional_info'], dict):
                        if 'exam' in ed['additional_info']:
                            ed['additional_info'].pop('exam', None)

                    # Convert year_of_completion to integer if it's a string with digits
                    if 'year_of_completion' in ed and isinstance(ed['year_of_completion'], str):
                        if ed['year_of_completion'].isdigit():
                            ed['year_of_completion'] = int(ed['year_of_completion'])
                        elif ed['year_of_completion'] == '[Year of Completion]':
                            # Use a default value for placeholder
                            ed['year_of_completion'] = 2023

            # Preprocess personal information if present
            if 'personal_information' in data and data['personal_information']:
                pi = data['personal_information']

                # Fix email format if it's a placeholder
                if 'email' in pi and pi['email'] and '[' in pi['email']:
                    pi['email'] = 'example@example.com'

                # Fix GitHub URL if it's a placeholder
                if 'github' in pi and pi['github'] and '[' in pi['github']:
                    pi['github'] = 'https://github.com/example'

                # Fix LinkedIn URL if it's a placeholder
                if 'linkedin' in pi and pi['linkedin'] and '[' in pi['linkedin']:
                    pi['linkedin'] = 'https://linkedin.com/in/example'

                # Fix zip code if it's too long
                if 'zip_code' in pi and pi['zip_code'] and len(pi['zip_code']) > 10:
                    pi['zip_code'] = pi['zip_code'][:10]

            # Preprocess projects if present
            if 'projects' in data and data['projects']:
                for project in data['projects']:
                    # Fix project link if it's a placeholder or missing
                    if 'link' not in project or not project['link']:
                        # Create a default link based on project name
                        if 'name' in project and project['name']:
                            project_name = project['name'].lower().replace(' ', '-')
                            project['link'] = f'https://github.com/example/{project_name}'
                        else:
                            project['link'] = 'https://github.com/example/project'
                    elif '[' in project['link'] or project['link'].startswith('#'):
                        # Replace placeholder links with real URLs
                        if 'name' in project and project['name']:
                            project_name = project['name'].lower().replace(' ', '-')
                            project['link'] = f'https://github.com/example/{project_name}'
                        else:
                            project['link'] = 'https://github.com/example/project'

            # Create an instance of Resume from the parsed data
            super().__init__(**data)
        except yaml.YAMLError as e:
            raise ValueError("Error parsing YAML file. Please check your YAML syntax.") from e
        except ValidationError as e:
            # More user-friendly validation error message
            error_msg = "Resume validation failed. Please check the following fields:\n"
            for error in e.errors():
                field = error['loc'][0] if error['loc'] else "Unknown field"
                if len(error['loc']) > 1:
                    field = ".".join(str(loc) for loc in error['loc'])
                error_msg += f"- {field}: {error['msg']}\n"
            raise ValueError(error_msg) from e
        except Exception as e:
            raise Exception(f"Unexpected error while parsing YAML: {e}") from e


    def _process_personal_information(self, data: Dict[str, Any]) -> PersonalInformation:
        try:
            return PersonalInformation(**data)
        except TypeError as e:
            raise TypeError(f"Invalid data for PersonalInformation: {e}") from e
        except AttributeError as e:
            raise AttributeError(f"AttributeError in PersonalInformation: {e}") from e
        except Exception as e:
            raise Exception(f"Unexpected error in PersonalInformation processing: {e}") from e

    def _process_education_details(self, data: List[Dict[str, Any]]) -> List[EducationDetails]:
        education_list = []
        for edu in data:
            try:
                # Extract location information if available
                location = None
                country = None

                # Check for location in additional_info
                if 'additional_info' in edu and isinstance(edu['additional_info'], dict):
                    if 'location' in edu['additional_info']:
                        location = edu['additional_info']['location']
                    if 'country' in edu['additional_info']:
                        country = edu['additional_info']['country']

                # Create education entry without exam field
                education = EducationDetails(
                    education_level=edu.get('education_level'),
                    institution=edu.get('institution'),
                    field_of_study=edu.get('field_of_study'),
                    final_evaluation_grade=edu.get('final_evaluation_grade'),
                    start_date=edu.get('start_date'),
                    year_of_completion=edu.get('year_of_completion'),
                    location=location,
                    country=country
                )
                education_list.append(education)
            except KeyError as e:
                raise KeyError(f"Missing field in education details: {e}") from e
            except TypeError as e:
                raise TypeError(f"Invalid data for Education: {e}") from e
            except AttributeError as e:
                raise AttributeError(f"AttributeError in Education: {e}") from e
            except Exception as e:
                raise Exception(f"Unexpected error in Education processing: {e}") from e
        return education_list

    def _process_experience_details(self, data: List[Dict[str, Any]]) -> List[ExperienceDetails]:
        experience_list = []
        for exp in data:
            try:
                # Process responsibilities with more robust error handling
                key_responsibilities = []
                resp_list = exp.get('key_responsibilities', [])

                if resp_list:
                    for resp in resp_list:
                        try:
                            # Handle different formats of responsibilities
                            if isinstance(resp, dict):
                                if 'responsibility' in resp:
                                    key_responsibilities.append(Responsibility(responsibility=resp['responsibility']))
                                elif len(resp) > 0:
                                    # Get the first value if it's a dict with any key
                                    key_responsibilities.append(Responsibility(description=list(resp.values())[0]))
                            elif isinstance(resp, str):
                                # Handle plain string responsibilities
                                key_responsibilities.append(Responsibility(description=resp))
                        except Exception as resp_err:
                            # Log error but continue processing other responsibilities
                            print(f"Error processing responsibility: {resp_err}")

                # Process skills with error handling
                skills_acquired = []
                try:
                    skills_acquired = [str(skill) for skill in exp.get('skills_acquired', [])]
                except Exception as skills_err:
                    print(f"Error processing skills: {skills_err}")

                # Create experience entry
                experience = ExperienceDetails(
                    position=exp.get('position', ''),
                    company=exp.get('company', ''),
                    employment_period=exp.get('employment_period', ''),
                    location=exp.get('location', ''),
                    industry=exp.get('industry', ''),
                    key_responsibilities=key_responsibilities,
                    skills_acquired=skills_acquired
                )
                experience_list.append(experience)
            except KeyError as e:
                raise KeyError(f"Missing field in experience details: {e}") from e
            except TypeError as e:
                raise TypeError(f"Invalid data for Experience: {e}") from e
            except AttributeError as e:
                raise AttributeError(f"AttributeError in Experience: {e}") from e
            except Exception as e:
                raise Exception(f"Unexpected error in Experience processing: {e}") from e
        return experience_list


# Removed Exam class as it's no longer needed

@dataclass
class Responsibility:
    description: str

    def __init__(self, description=None, responsibility=None):
        """
        Initialize with either description or responsibility parameter.
        This makes the class more flexible for different field names.
        """
        self.description = description or responsibility or ""
        self.responsibility = self.description  # Alias for compatibility