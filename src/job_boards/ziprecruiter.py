import time
import uuid
import re
from typing import List, Dict, Any
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.support.ui import Select

from src.job import Job
from src.job_application import JobApplication
from src.job_boards.job_board_interface import JobBoardInterface
from src.logging import logger


class ZipRecruiter(JobBoardInterface):
    """ZipRecruiter job board implementation"""
    
    def search_jobs(self, keywords: List[str], location: str, filters: Dict[str, Any]) -> List[Job]:
        """Search for jobs on ZipRecruiter"""
        jobs = []
        search_query = "+".join(keywords)
        
        # Build search URL with filters
        url = f"https://www.ziprecruiter.com/jobs-search?search={search_query}&location={location}"
        
        # Add remote filter if specified
        if filters.get("remote"):
            url += "&refine_by_location_type=only_remote"
            
        # Add date posted filter
        if filters.get("date", {}).get("24_hours"):
            url += "&days=1"
        elif filters.get("date", {}).get("week"):
            url += "&days=7"
        elif filters.get("date", {}).get("month"):
            url += "&days=30"
            
        logger.info(f"Searching ZipRecruiter with URL: {url}")
        self.driver.get(url)
        
        try:
            # Wait for job cards to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "article.job_result"))
            )
            
            # Extract job listings
            job_cards = self.driver.find_elements(By.CSS_SELECTOR, "article.job_result")
            
            for card in job_cards:
                try:
                    job = Job()
                    job.role = card.find_element(By.CSS_SELECTOR, "h2.job_title").text
                    job.company = card.find_element(By.CSS_SELECTOR, "a.hiring_company_text").text
                    job.location = card.find_element(By.CSS_SELECTOR, "div.location").text
                    
                    # Get job link
                    job_link_element = card.find_element(By.CSS_SELECTOR, "a.job_link")
                    job.link = job_link_element.get_attribute("href")
                    
                    # Extract job ID from URL
                    job_id_match = re.search(r"job/([^/]+)", job.link)
                    if job_id_match:
                        job.id = job_id_match.group(1)
                    else:
                        job.id = str(uuid.uuid4())
                    
                    # Check if job matches blacklist criteria
                    if self._is_blacklisted(job, filters):
                        continue
                        
                    jobs.append(job)
                except Exception as e:
                    logger.error(f"Error extracting job details: {e}")
                    continue
                    
            return jobs
            
        except TimeoutException:
            logger.error("Timeout waiting for ZipRecruiter job results to load")
            return []
    
    def apply_to_job(self, job: Job, job_application: JobApplication) -> bool:
        """Apply to a job on ZipRecruiter"""
        try:
            # Navigate to job page
            self.driver.get(job.link)
            
            # Wait for apply button
            apply_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.apply_now_link, a.apply_now_link"))
            )
            
            # Check if it's an "Apply on company site" button
            if "Apply on company site" in apply_button.text:
                job.apply_method = "external"
                logger.info(f"Job requires application on company site: {job.link}")
                return False
                
            # Click apply button
            apply_button.click()
            
            # Wait for application form
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.application_form"))
            )
            
            # Fill out application form
            self._fill_application_form(job_application)
            
            # Submit application
            submit_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))
            )
            submit_button.click()
            
            # Wait for confirmation
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.application_success"))
            )
            
            logger.info(f"Successfully applied to job: {job.role} at {job.company}")
            return True
            
        except Exception as e:
            logger.error(f"Error applying to job {job.link}: {e}")
            return False
            
    def is_already_applied(self, job: Job) -> bool:
        """Check if already applied to this job"""
        try:
            self.driver.get(job.link)
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.job_details"))
            )
            
            # Check for "Applied" indicator
            applied_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Applied')]")
            return len(applied_elements) > 0
            
        except Exception as e:
            logger.error(f"Error checking if already applied: {e}")
            return False
    
    def get_job_details(self, job_url: str) -> Job:
        """Get detailed job information"""
        try:
            self.driver.get(job_url)
            
            # Wait for job details to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.job_details"))
            )
            
            job = Job()
            job.link = job_url
            
            # Extract job ID from URL
            job_id_match = re.search(r"job/([^/]+)", job_url)
            if job_id_match:
                job.id = job_id_match.group(1)
            else:
                job.id = str(uuid.uuid4())
            
            # Extract job details
            job.role = self.driver.find_element(By.CSS_SELECTOR, "h1.job_title").text
            job.company = self.driver.find_element(By.CSS_SELECTOR, "a.hiring_company_text").text
            job.location = self.driver.find_element(By.CSS_SELECTOR, "div.location").text
            
            # Get job description
            description_element = self.driver.find_element(By.CSS_SELECTOR, "div.job_description")
            job.description = description_element.text
            
            return job
            
        except Exception as e:
            logger.error(f"Error getting job details: {e}")
            return Job()
    
    def _fill_application_form(self, job_application: JobApplication) -> None:
        """Fill out ZipRecruiter application form"""
        try:
            # Fill personal information
            self._fill_text_field("input#applicant_name", f"{job_application.personal_info.name} {job_application.personal_info.surname}")
            self._fill_text_field("input#applicant_email", job_application.personal_info.email)
            self._fill_text_field("input#applicant_phone", f"{job_application.personal_info.phone_prefix}{job_application.personal_info.phone}")
            
            # Upload resume
            if job_application.resume_path:
                resume_upload = self.driver.find_element(By.CSS_SELECTOR, "input#resume_upload")
                resume_upload.send_keys(job_application.resume_path)
                
            # Upload cover letter if requested
            cover_letter_field = self.driver.find_elements(By.CSS_SELECTOR, "input#cover_letter_upload")
            if cover_letter_field and job_application.cover_letter_path:
                cover_letter_field[0].send_keys(job_application.cover_letter_path)
                
            # Handle additional questions if present
            self._answer_additional_questions(job_application)
            
        except Exception as e:
            logger.error(f"Error filling application form: {e}")
            raise
    
    def _answer_additional_questions(self, job_application: JobApplication) -> None:
        """Answer additional application questions"""
        # Find all question containers
        question_containers = self.driver.find_elements(By.CSS_SELECTOR, "div.application_question")
        
        for container in question_containers:
            try:
                question_text = container.find_element(By.CSS_SELECTOR, "label.question_label").text
                
                # Determine question type and answer accordingly
                if container.find_elements(By.CSS_SELECTOR, "input[type='text']"):
                    # Text input question
                    input_field = container.find_element(By.CSS_SELECTOR, "input[type='text']")
                    answer = self._get_ai_answer(question_text, job_application)
                    input_field.send_keys(answer)
                    
                elif container.find_elements(By.CSS_SELECTOR, "select"):
                    # Dropdown question
                    select_field = container.find_element(By.CSS_SELECTOR, "select")
                    # Choose appropriate option based on question
                    if "years of experience" in question_text.lower():
                        self._select_option(select_field, "3-5 years")
                    elif "education" in question_text.lower():
                        self._select_option(select_field, "Bachelor's")
                    else:
                        # Default to first non-empty option
                        options = select_field.find_elements(By.CSS_SELECTOR, "option")
                        for option in options[1:]:  # Skip first option which is usually empty
                            option.click()
                            break
                            
                elif container.find_elements(By.CSS_SELECTOR, "input[type='radio']"):
                    # Radio button question
                    radio_buttons = container.find_elements(By.CSS_SELECTOR, "input[type='radio']")
                    # For yes/no questions, usually select "Yes" for positive questions
                    if "willing" in question_text.lower() or "able" in question_text.lower():
                        radio_buttons[0].click()  # Usually first option is "Yes"
                    
            except Exception as e:
                logger.error(f"Error answering question '{question_text}': {e}")
                continue
    
    def _get_ai_answer(self, question: str, job_application: JobApplication) -> str:
        """Get AI-generated answer for application question"""
        # This would integrate with the existing LLM manager
        # For now, return placeholder answers based on question type
        question_lower = question.lower()
        
        if "salary" in question_lower or "compensation" in question_lower:
            return job_application.salary_expectations.salary_range_usd
        elif "start" in question_lower or "available" in question_lower:
            return job_application.availability.notice_period
        elif "experience" in question_lower:
            return "I have 3+ years of relevant experience in this field."
        elif "why" in question_lower and "company" in question_lower:
            return f"I'm excited about {job_application.job.company}'s innovative approach and industry leadership."
        else:
            return "Please refer to my resume and cover letter for detailed information."
    
    def _fill_text_field(self, selector: str, value: str) -> None:
        """Fill a text field with given value"""
        try:
            field = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            field.clear()
            field.send_keys(value)
        except TimeoutException:
            # Field might not be present in this form
            pass
    
    def _select_option(self, select_element, option_text: str) -> None:
        """Select option from dropdown by text"""
        select = Select(select_element)
        try:
            select.select_by_visible_text(option_text)
        except NoSuchElementException:
            # If exact match not found, try to find closest option
            options = select.options
            for option in options:
                if option.text and option_text.lower() in option.text.lower():
                    option.click()
                    break
    
    def _is_blacklisted(self, job: Job, filters: Dict[str, Any]) -> bool:
        """Check if job matches blacklist criteria"""
        # Check company blacklist
        if filters.get("company_blacklist"):
            for blacklisted in filters["company_blacklist"]:
                if blacklisted.lower() in job.company.lower():
                    return True
        
        # Check title blacklist
        if filters.get("title_blacklist"):
            for blacklisted in filters["title_blacklist"]:
                if blacklisted.lower() in job.role.lower():
                    return True
        
        # Check location blacklist
        if filters.get("location_blacklist"):
            for blacklisted in filters["location_blacklist"]:
                if blacklisted.lower() in job.location.lower():
                    return True
        
        return False
