import time
import uuid
import random
from typing import List, Dict, Any
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.support.ui import Select

from src.job import Job
from src.job_application import JobApplication
from src.job_boards.job_board_interface import JobBoardInterface
from src.logging import logger


class Indeed(JobBoardInterface):
    """Indeed job board implementation with Cloudflare bypass capabilities"""

    def __init__(self, driver: WebDriver):
        super().__init__(driver)
        self.cloudflare_detected = False
        self.max_retries = 3
        self.manual_mode = False
        self.manual_mode_confirmed = False

    def _handle_cloudflare(self, timeout=120):
        """Handle Cloudflare challenges by waiting for user to solve them manually"""
        try:
            self.cloudflare_detected = True

            # If this is the first time we're seeing Cloudflare, offer manual mode
            if not self.manual_mode_confirmed:
                print("\n" + "="*80)
                print("CLOUDFLARE PROTECTION DETECTED")
                print("Indeed is using strong anti-bot measures that require manual intervention.")
                print("\nOptions:")
                print("1. Solve the CAPTCHA manually in the browser window")
                print("2. Switch to manual search mode (recommended)")
                print("\nIn manual search mode, the browser will open and you can:")
                print("- Search for jobs manually")
                print("- Navigate through search results")
                print("- The tool will track which jobs you view")
                print("="*80)

                choice = input("\nEnter your choice (1 or 2): ")
                if choice == "2":
                    self.manual_mode = True
                    self.manual_mode_confirmed = True
                    print("\nSwitching to manual search mode. Please use the browser to search for jobs.")
                    print("The tool will continue running in the background to track your activity.")
                    print("When you're done, close the browser or press Ctrl+C in this terminal.")
                    return True
                else:
                    self.manual_mode_confirmed = True
                    print("\nContinuing with automatic mode. Please solve the CAPTCHA in the browser window.")

            if self.manual_mode:
                # In manual mode, we just wait for the user to do their thing
                print("\nManual mode active. Please use the browser to search for jobs.")
                print("The tool will continue running in the background.")
                time.sleep(timeout)  # Just wait for a long time
                return True

            # Standard Cloudflare handling for automatic mode
            logger.info("Cloudflare challenge detected. Please solve the CAPTCHA manually in the browser window.")
            logger.info(f"Waiting up to {timeout} seconds for Cloudflare verification to complete...")

            # Wait for the page to load after Cloudflare verification
            start_time = time.time()
            while time.time() - start_time < timeout:
                # Check if we're still on Cloudflare page
                if "cloudflare" in self.driver.current_url.lower() or "challenge" in self.driver.current_url.lower():
                    time.sleep(2)
                    continue

                # Try to find an element that would be present on the Indeed page
                try:
                    WebDriverWait(self.driver, 2).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "div.jobsearch-JobCountAndSortPane-jobCount, div.job_seen_beacon"))
                    )
                    logger.info("Cloudflare verification completed successfully.")
                    return True
                except:
                    # Not yet loaded, continue waiting
                    time.sleep(2)

            # If we're still here, offer manual mode again
            if not self.manual_mode:
                print("\n" + "="*80)
                print("CLOUDFLARE VERIFICATION TIMED OUT")
                print("Would you like to switch to manual search mode?")
                print("="*80)
                choice = input("\nSwitch to manual mode? (y/n): ")
                if choice.lower() == "y":
                    self.manual_mode = True
                    print("\nSwitching to manual search mode. Please use the browser to search for jobs.")
                    return True

            logger.error(f"Cloudflare verification timed out after {timeout} seconds.")
            return False
        except Exception as e:
            logger.error(f"Error handling Cloudflare: {e}")
            return False

    def _retry_with_delay(self, func, *args, **kwargs):
        """Retry a function with exponential backoff"""
        retry_count = 0
        last_exception = None

        while retry_count < self.max_retries:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                retry_count += 1
                if retry_count >= self.max_retries:
                    logger.error(f"Failed after {self.max_retries} retries: {e}")
                    break

                # Calculate delay with exponential backoff (2^retry_count seconds)
                delay = 2 ** retry_count + random.uniform(0, 1)
                logger.info(f"Retrying after {delay:.2f} seconds (attempt {retry_count+1}/{self.max_retries})...")
                time.sleep(delay)

        # If we get here, all retries failed
        if last_exception:
            logger.error(f"All retries failed: {last_exception}")

        # Return appropriate default value based on function name
        if func.__name__ == '_do_search_jobs':
            return []
        elif func.__name__ == '_do_apply_to_job':
            return False
        elif func.__name__ == '_do_check_if_applied':
            return False
        elif func.__name__ == '_do_get_job_details':
            return Job()
        else:
            # Default fallback
            return None

    def search_jobs(self, keywords: List[str], location: str, filters: Dict[str, Any]) -> List[Job]:
        """Search for jobs on Indeed with retry mechanism"""
        try:
            # Use retry mechanism for the search
            return self._retry_with_delay(self._do_search_jobs, keywords, location, filters)
        except Exception as e:
            logger.error(f"Failed to search jobs on Indeed: {e}")
            return []

    def _do_search_jobs(self, keywords: List[str], location: str, filters: Dict[str, Any]) -> List[Job]:
        """Internal method to search for jobs on Indeed"""
        jobs = []
        search_query = "+".join(keywords)

        # Build search URL with filters
        url = f"https://www.indeed.com/jobs?q={search_query}&l={location}"

        # Add experience level filter if specified
        if filters.get("experience_level"):
            experience_params = self._map_experience_level(filters["experience_level"])
            if experience_params:
                url += f"&explvl={experience_params}"

        # Add remote filter if specified
        if filters.get("remote"):
            url += "&remotejob=032b3046-06a3-4876-8dfd-474eb5e7ed11"

        # Add date posted filter
        if filters.get("date", {}).get("24_hours"):
            url += "&fromage=1"
        elif filters.get("date", {}).get("week"):
            url += "&fromage=7"
        elif filters.get("date", {}).get("month"):
            url += "&fromage=30"

        logger.info(f"Searching Indeed with URL: {url}")
        self.driver.get(url)

        # Check for Cloudflare challenge
        try:
            # First try to wait for job cards with a short timeout
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.job_seen_beacon"))
            )
        except TimeoutException:
            # If we hit a timeout, check if we're on a Cloudflare page
            if "cloudflare" in self.driver.current_url.lower() or "challenge" in self.driver.title.lower():
                # Handle Cloudflare challenge
                if not self._handle_cloudflare(timeout=120):
                    logger.error("Failed to bypass Cloudflare protection")
                    return []

            # If we're in manual mode, just return an empty list for now
            # The user will be interacting with the browser directly
            if self.manual_mode:
                print("\nManual mode active. Please use the browser to search for jobs.")
                print("The tool will track which jobs you view and can apply to them later.")
                print("When you're done, close the browser or press Ctrl+C in this terminal.")

                # Wait for a long time to let the user browse
                try:
                    # Keep checking for job views in the background
                    start_time = time.time()
                    while time.time() - start_time < 3600:  # Wait up to an hour
                        # Check if we can detect any job cards now
                        try:
                            job_cards = self.driver.find_elements(By.CSS_SELECTOR, "div.job_seen_beacon")
                            if job_cards:
                                # Process any visible job cards
                                for card in job_cards:
                                    try:
                                        job = Job()
                                        job.role = card.find_element(By.CSS_SELECTOR, "h2.jobTitle").text
                                        job.company = card.find_element(By.CSS_SELECTOR, "span.companyName").text
                                        job.location = card.find_element(By.CSS_SELECTOR, "div.companyLocation").text

                                        # Get job link
                                        job_link_element = card.find_element(By.CSS_SELECTOR, "h2.jobTitle a")
                                        job_id = job_link_element.get_attribute("data-jk")
                                        job.link = f"https://www.indeed.com/viewjob?jk={job_id}"
                                        job.id = job_id

                                        # Check if job matches blacklist criteria
                                        if self._is_blacklisted(job, filters):
                                            continue

                                        # Check if we already have this job
                                        if not any(j.id == job.id for j in jobs):
                                            jobs.append(job)
                                            print(f"Detected job: {job.role} at {job.company}")
                                    except Exception as e:
                                        # Ignore errors in manual mode
                                        pass
                        except:
                            # Ignore errors in manual mode
                            pass

                        # Check if we're on a job details page
                        if "viewjob" in self.driver.current_url:
                            try:
                                # Extract job ID from URL
                                job_id = self.driver.current_url.split("jk=")[1].split("&")[0]

                                # Check if we already have this job
                                if not any(j.id == job_id for j in jobs):
                                    # Create a new job
                                    job = Job()
                                    job.id = job_id
                                    job.link = self.driver.current_url

                                    # Try to extract job details
                                    try:
                                        job.role = self.driver.find_element(By.CSS_SELECTOR, "h1.jobsearch-JobInfoHeader-title").text
                                    except:
                                        job.role = "Unknown Position"

                                    try:
                                        job.company = self.driver.find_element(By.CSS_SELECTOR, "div.jobsearch-InlineCompanyRating div").text
                                    except:
                                        job.company = "Unknown Company"

                                    try:
                                        job.location = self.driver.find_element(By.CSS_SELECTOR, "div.jobsearch-JobInfoHeader-subtitle div").text
                                    except:
                                        job.location = "Unknown Location"

                                    jobs.append(job)
                                    print(f"Viewing job: {job.role} at {job.company}")
                            except:
                                # Ignore errors in manual mode
                                pass

                        time.sleep(5)  # Check every 5 seconds
                except KeyboardInterrupt:
                    print("\nManual browsing interrupted. Processing found jobs...")

                return jobs

            # After Cloudflare handling (or if no Cloudflare), wait for job cards again
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.job_seen_beacon"))
                )
            except TimeoutException:
                logger.error("Could not find job cards even after Cloudflare handling")
                return []

        # Extract job listings
        job_cards = self.driver.find_elements(By.CSS_SELECTOR, "div.job_seen_beacon")

        for card in job_cards:
            try:
                job = Job()
                job.role = card.find_element(By.CSS_SELECTOR, "h2.jobTitle").text
                job.company = card.find_element(By.CSS_SELECTOR, "span.companyName").text
                job.location = card.find_element(By.CSS_SELECTOR, "div.companyLocation").text

                # Get job link
                job_link_element = card.find_element(By.CSS_SELECTOR, "h2.jobTitle a")
                job_id = job_link_element.get_attribute("data-jk")
                job.link = f"https://www.indeed.com/viewjob?jk={job_id}"
                job.id = job_id

                # Check if job matches blacklist criteria
                if self._is_blacklisted(job, filters):
                    continue

                jobs.append(job)
            except Exception as e:
                logger.error(f"Error extracting job details: {e}")
                continue

        return jobs

    def apply_to_job(self, job: Job, job_application: JobApplication) -> bool:
        """Apply to a job on Indeed with retry mechanism"""
        try:
            # Use retry mechanism for the application
            return self._retry_with_delay(self._do_apply_to_job, job, job_application)
        except Exception as e:
            logger.error(f"Failed to apply to job on Indeed: {e}")
            return False

    def _do_apply_to_job(self, job: Job, job_application: JobApplication) -> bool:
        """Internal method to apply to a job on Indeed"""
        try:
            # If we're in manual mode, guide the user through the application process
            if self.manual_mode:
                print("\n" + "="*80)
                print(f"MANUAL APPLICATION MODE: {job.role} at {job.company}")
                print("="*80)
                print(f"\nOpening job page: {job.link}")

                # Navigate to job page
                self.driver.get(job.link)

                # Check for Cloudflare challenge
                if "cloudflare" in self.driver.current_url.lower() or "challenge" in self.driver.title.lower():
                    print("\nCloudflare challenge detected. Please solve the CAPTCHA in the browser window.")
                    input("Press Enter when you've solved the CAPTCHA...")

                print("\nPlease complete the application process manually in the browser.")
                print("The tool will track your progress and record the application.")

                # Wait for user to complete the application
                completed = input("\nDid you complete the application? (y/n): ")
                if completed.lower() == 'y':
                    print("Application recorded as successful.")
                    return True
                else:
                    print("Application recorded as unsuccessful.")
                    return False

            # Regular automated mode
            # Navigate to job page
            self.driver.get(job.link)

            # Check for Cloudflare challenge
            try:
                # First try to wait for apply button with a short timeout
                apply_button = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button[id='indeedApplyButton']"))
                )
            except TimeoutException:
                # If we hit a timeout, check if we're on a Cloudflare page
                if "cloudflare" in self.driver.current_url.lower() or "challenge" in self.driver.title.lower():
                    # Handle Cloudflare challenge
                    if not self._handle_cloudflare(timeout=60):
                        logger.error("Failed to bypass Cloudflare protection")
                        return False

                # After Cloudflare handling (or if no Cloudflare), wait for apply button again
                apply_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button[id='indeedApplyButton']"))
                )

            # Check if it's an "Apply on company site" button
            if "Apply on company site" in apply_button.text:
                job.apply_method = "external"
                logger.info(f"Job requires application on company site: {job.link}")
                return False

            # Click apply button
            apply_button.click()

            # Switch to application iframe
            WebDriverWait(self.driver, 10).until(
                EC.frame_to_be_available_and_switch_to_it((By.ID, "indeedapply-iframe"))
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
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.ia-Success-card"))
            )

            logger.info(f"Successfully applied to job: {job.role} at {job.company}")
            return True

        except Exception as e:
            logger.error(f"Error applying to job {job.link}: {e}")
            return False

    def is_already_applied(self, job: Job) -> bool:
        """Check if already applied to this job with retry mechanism"""
        try:
            # Use retry mechanism for checking application status
            return self._retry_with_delay(self._do_check_if_applied, job)
        except Exception as e:
            logger.error(f"Failed to check if already applied on Indeed: {e}")
            return False

    def _do_check_if_applied(self, job: Job) -> bool:
        """Internal method to check if already applied to a job on Indeed"""
        try:
            self.driver.get(job.link)

            # Check for Cloudflare challenge
            try:
                # First try to wait for job info with a short timeout
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.jobsearch-JobInfoHeader"))
                )
            except TimeoutException:
                # If we hit a timeout, check if we're on a Cloudflare page
                if "cloudflare" in self.driver.current_url.lower() or "challenge" in self.driver.title.lower():
                    # Handle Cloudflare challenge
                    if not self._handle_cloudflare(timeout=60):
                        logger.error("Failed to bypass Cloudflare protection")
                        return False

                # After Cloudflare handling (or if no Cloudflare), wait for job info again
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.jobsearch-JobInfoHeader"))
                )

            # Check for "Applied" indicator
            applied_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Applied')]")
            return len(applied_elements) > 0

        except Exception as e:
            logger.error(f"Error checking if already applied: {e}")
            return False

    def get_job_details(self, job_url: str) -> Job:
        """Get detailed job information with retry mechanism"""
        try:
            # Use retry mechanism for getting job details
            return self._retry_with_delay(self._do_get_job_details, job_url)
        except Exception as e:
            logger.error(f"Failed to get job details on Indeed: {e}")
            return Job()

    def _do_get_job_details(self, job_url: str) -> Job:
        """Internal method to get detailed job information from Indeed"""
        try:
            self.driver.get(job_url)

            # Check for Cloudflare challenge
            try:
                # First try to wait for job details with a short timeout
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.jobsearch-JobComponent"))
                )
            except TimeoutException:
                # If we hit a timeout, check if we're on a Cloudflare page
                if "cloudflare" in self.driver.current_url.lower() or "challenge" in self.driver.title.lower():
                    # Handle Cloudflare challenge
                    if not self._handle_cloudflare(timeout=60):
                        logger.error("Failed to bypass Cloudflare protection")
                        return Job()

                # After Cloudflare handling (or if no Cloudflare), wait for job details again
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.jobsearch-JobComponent"))
                )

            job = Job()
            job.link = job_url

            # Extract job ID from URL
            import re
            job_id_match = re.search(r"jk=([^&]+)", job_url)
            if job_id_match:
                job.id = job_id_match.group(1)
            else:
                job.id = str(uuid.uuid4())

            # Extract job details
            job.role = self.driver.find_element(By.CSS_SELECTOR, "h1.jobsearch-JobInfoHeader-title").text
            job.company = self.driver.find_element(By.CSS_SELECTOR, "div[data-company-name='true']").text
            job.location = self.driver.find_element(By.CSS_SELECTOR, "div[data-testid='job-location']").text

            # Get job description
            description_element = self.driver.find_element(By.CSS_SELECTOR, "div#jobDescriptionText")
            job.description = description_element.text

            return job

        except Exception as e:
            logger.error(f"Error getting job details: {e}")
            return Job()

    def _fill_application_form(self, job_application: JobApplication) -> None:
        """Fill out Indeed application form"""
        try:
            # Fill personal information
            self._fill_text_field("input#input-applicant\\.name", f"{job_application.personal_info.name} {job_application.personal_info.surname}")
            self._fill_text_field("input#input-applicant\\.email", job_application.personal_info.email)
            self._fill_text_field("input#input-applicant\\.phone", f"{job_application.personal_info.phone_prefix}{job_application.personal_info.phone}")

            # Upload resume
            if job_application.resume_path:
                resume_upload = self.driver.find_element(By.CSS_SELECTOR, "input#resume-upload-input")
                resume_upload.send_keys(job_application.resume_path)

            # Upload cover letter if requested
            cover_letter_field = self.driver.find_elements(By.CSS_SELECTOR, "input#cover-letter-upload-input")
            if cover_letter_field and job_application.cover_letter_path:
                cover_letter_field[0].send_keys(job_application.cover_letter_path)

            # Handle additional questions if present
            self._answer_additional_questions(job_application)

        except Exception as e:
            logger.error(f"Error filling application form: {e}")
            raise

    def _answer_additional_questions(self, job_application: JobApplication) -> None:
        """Answer additional application questions using AI"""
        # Find all question containers
        question_containers = self.driver.find_elements(By.CSS_SELECTOR, "div.ia-Questions-item")

        for container in question_containers:
            try:
                question_text = container.find_element(By.CSS_SELECTOR, "label.ia-Questions-item-label").text

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

    def _map_experience_level(self, experience_level: Dict[str, bool]) -> str:
        """Map experience level preferences to Indeed parameters"""
        if experience_level.get("entry"):
            return "entry_level"
        elif experience_level.get("mid_senior_level"):
            return "mid_level"
        elif experience_level.get("director") or experience_level.get("executive"):
            return "senior_level"
        return ""

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
