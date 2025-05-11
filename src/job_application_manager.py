import os
import time
import random
import base64
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime, timedelta

from src.job import Job
from src.job_application import JobApplication
from src.job_application_tracker import JobApplicationTracker
from src.job_boards.job_board_factory import JobBoardFactory
from src.job_boards.job_board_interface import JobBoardInterface
from src.libs.resume_and_cover_builder.resume_facade import ResumeFacade
from src.utils.chrome_utils import init_browser
from src.logging import logger
from config import (
    JOB_MAX_APPLICATIONS,
    JOB_MIN_APPLICATIONS,
    JOB_SUITABILITY_SCORE
)


class JobApplicationManager:
    """Manages the entire job application process"""
    
    def __init__(self, resume_facade: ResumeFacade, work_preferences: Dict[str, Any]):
        """Initialize the job application manager"""
        self.resume_facade = resume_facade
        self.work_preferences = work_preferences
        self.tracker = JobApplicationTracker()
        self.driver = init_browser()
        
        # Create output directory for generated files
        self.output_dir = Path("data_folder/output")
        os.makedirs(self.output_dir, exist_ok=True)
    
    def run_application_cycle(self, job_boards: List[str], max_applications: int = None) -> Dict[str, Any]:
        """Run a complete job application cycle"""
        if max_applications is None:
            # Use random number between min and max if not specified
            max_applications = random.randint(JOB_MIN_APPLICATIONS, JOB_MAX_APPLICATIONS)
            
        logger.info(f"Starting job application cycle. Target: {max_applications} applications")
        
        results = {
            "applications_attempted": 0,
            "applications_successful": 0,
            "applications_failed": 0,
            "jobs_found": 0,
            "jobs_skipped": 0,
            "errors": []
        }
        
        # Process each job board
        for board_name in job_boards:
            try:
                # Check if we've reached the maximum applications
                if results["applications_successful"] >= max_applications:
                    logger.info(f"Reached target of {max_applications} applications. Stopping cycle.")
                    break
                
                # Create job board instance
                job_board = JobBoardFactory.create(board_name, self.driver)
                logger.info(f"Processing job board: {board_name}")
                
                # Search for jobs
                jobs = self._search_jobs(job_board)
                results["jobs_found"] += len(jobs)
                
                # Process each job
                for job in jobs:
                    # Check if we've reached the maximum applications
                    if results["applications_successful"] >= max_applications:
                        break
                        
                    # Process the job
                    success = self._process_job(job_board, job)
                    
                    if success:
                        results["applications_successful"] += 1
                    else:
                        results["applications_failed"] += 1
                        
                    results["applications_attempted"] += 1
                    
                    # Add random delay between applications (2-5 minutes)
                    delay = random.randint(120, 300)
                    logger.info(f"Waiting {delay} seconds before next application...")
                    time.sleep(delay)
                    
            except Exception as e:
                error_msg = f"Error processing job board {board_name}: {str(e)}"
                logger.error(error_msg)
                results["errors"].append(error_msg)
        
        # Close the browser when done
        self.driver.quit()
        
        # Log results
        logger.info(f"Application cycle completed. Results: {results}")
        return results
    
    def _search_jobs(self, job_board: JobBoardInterface) -> List[Job]:
        """Search for jobs on the given job board"""
        # Extract search parameters from work preferences
        keywords = self.work_preferences.get("positions", [])
        location = self.work_preferences.get("locations", ["Remote"])[0]
        filters = {
            "remote": self.work_preferences.get("remote", True),
            "experience_level": self.work_preferences.get("experience_level", {}),
            "company_blacklist": self.work_preferences.get("company_blacklist", []),
            "title_blacklist": self.work_preferences.get("title_blacklist", []),
            "location_blacklist": self.work_preferences.get("location_blacklist", []),
            "date": self.work_preferences.get("date", {"week": True})
        }
        
        # Search for jobs
        jobs = job_board.search_jobs(keywords, location, filters)
        logger.info(f"Found {len(jobs)} jobs on {job_board.name}")
        
        # Filter out jobs we've already applied to
        filtered_jobs = []
        for job in jobs:
            # Get full job details
            detailed_job = job_board.get_job_details(job.link)
            
            # Check if we've already applied
            if job_board.is_already_applied(detailed_job):
                logger.info(f"Already applied to {detailed_job.role} at {detailed_job.company}. Skipping.")
                continue
                
            # Check job suitability
            suitability_score = self._calculate_job_suitability(detailed_job)
            if suitability_score < JOB_SUITABILITY_SCORE:
                logger.info(f"Job {detailed_job.role} at {detailed_job.company} has low suitability score ({suitability_score}). Skipping.")
                continue
                
            filtered_jobs.append(detailed_job)
            
        logger.info(f"After filtering, {len(filtered_jobs)} jobs remain eligible for application")
        return filtered_jobs
    
    def _process_job(self, job_board: JobBoardInterface, job: Job) -> bool:
        """Process a single job application"""
        try:
            logger.info(f"Processing job: {job.role} at {job.company}")
            
            # Generate tailored resume and cover letter
            resume_path, cover_letter_path = self._generate_application_documents(job)
            
            # Create job application object
            job_application = JobApplication()
            job_application.job = job
            job_application.resume_path = resume_path
            job_application.cover_letter_path = cover_letter_path
            
            # Set personal info from resume
            job_application.personal_info = self.resume_facade.resume_generator.resume_object.personal_information
            
            # Apply to the job
            success = job_board.apply_to_job(job, job_application)
            
            # Track the application
            status = "applied" if success else "failed"
            self.tracker.add_application(job_application, status)
            
            # Set follow-up date (2 weeks from now)
            if success:
                follow_up_date = datetime.now() + timedelta(days=14)
                self.tracker.set_follow_up_date(job.id, follow_up_date)
                
            return success
            
        except Exception as e:
            logger.error(f"Error processing job {job.role} at {job.company}: {e}")
            return False
    
    def _generate_application_documents(self, job: Job) -> Tuple[str, str]:
        """Generate tailored resume and cover letter for the job"""
        # Set the job in the resume facade
        self.resume_facade.set_driver(self.driver)
        
        # Create unique filenames based on job details
        job_hash = hashlib.md5(f"{job.company}_{job.role}".encode()).hexdigest()[:8]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = f"{job_hash}_{timestamp}"
        
        # Generate resume
        self.resume_facade.job = job
        resume_result, _ = self.resume_facade.create_resume_pdf_job_tailored()
        resume_path = os.path.join(self.output_dir, f"{base_filename}_resume.pdf")
        with open(resume_path, "wb") as f:
            f.write(base64.b64decode(resume_result))
        
        # Generate cover letter
        cover_letter_result, _ = self.resume_facade.create_cover_letter()
        cover_letter_path = os.path.join(self.output_dir, f"{base_filename}_cover_letter.pdf")
        with open(cover_letter_path, "wb") as f:
            f.write(base64.b64decode(cover_letter_result))
        
        return resume_path, cover_letter_path
    
    def _calculate_job_suitability(self, job: Job) -> int:
        """Calculate how suitable a job is based on our preferences"""
        score = 0
        
        # Check if job title matches our preferred titles
        for title in self.work_preferences.get("positions", []):
            if title.lower() in job.role.lower():
                score += 3
                break
                
        # Check for remote work if that's our preference
        if self.work_preferences.get("remote", True):
            if "remote" in job.location.lower():
                score += 2
                
        # Check for preferred skills in job description
        for skill in self.work_preferences.get("skills", []):
            if skill.lower() in job.description.lower():
                score += 1
                
        # Check for red flags in job description
        red_flags = ["unpaid", "commission only", "MLM", "multi-level"]
        for flag in red_flags:
            if flag.lower() in job.description.lower():
                score -= 5
                
        return score
