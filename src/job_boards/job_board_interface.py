from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from selenium.webdriver.remote.webdriver import WebDriver

from src.job import Job
from src.job_application import JobApplication


class JobBoardInterface(ABC):
    """Abstract interface for job board implementations"""
    
    def __init__(self, driver: WebDriver):
        self.driver = driver
        self.name = self.__class__.__name__
    
    @abstractmethod
    def search_jobs(self, keywords: List[str], location: str, filters: Dict[str, Any]) -> List[Job]:
        """Search for jobs with given parameters"""
        pass
    
    @abstractmethod
    def apply_to_job(self, job: Job, job_application: JobApplication) -> bool:
        """Apply to a specific job"""
        pass
    
    @abstractmethod
    def is_already_applied(self, job: Job) -> bool:
        """Check if already applied to this job"""
        pass
    
    @abstractmethod
    def get_job_details(self, job_url: str) -> Job:
        """Get detailed job information"""
        pass
