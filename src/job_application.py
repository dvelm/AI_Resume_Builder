from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime

from src.job import Job
from src.resume_schemas.resume import PersonalInformation


@dataclass
class SalaryExpectations:
    """Salary expectations for a job application"""
    salary_range_usd: str = "Negotiable based on the role and responsibilities"
    minimum_acceptable: float = 0.0
    target: float = 0.0


@dataclass
class Availability:
    """Availability information for a job application"""
    available_immediately: bool = True
    notice_period: str = "2 weeks"
    preferred_start_date: Optional[datetime] = None


@dataclass
class JobApplication:
    """Represents a job application"""
    job: Job = field(default_factory=Job)
    personal_info: PersonalInformation = field(default_factory=PersonalInformation)
    resume_path: str = ""
    cover_letter_path: str = ""
    salary_expectations: SalaryExpectations = field(default_factory=SalaryExpectations)
    availability: Availability = field(default_factory=Availability)
    application_date: Optional[datetime] = None
    status: str = "draft"  # draft, applied, interview, rejected, offer, accepted
    notes: List[Dict[str, Any]] = field(default_factory=list)
    application: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize application date if not provided"""
        if self.application_date is None:
            self.application_date = datetime.now()

    def add_note(self, note: str) -> None:
        """Add a note to the application"""
        self.notes.append({
            "date": datetime.now().isoformat(),
            "text": note
        })

    def update_status(self, status: str) -> None:
        """Update the application status"""
        valid_statuses = ["draft", "applied", "interview_scheduled", "interview_completed",
                         "rejected", "offer_received", "accepted", "declined"]

        if status not in valid_statuses:
            raise ValueError(f"Invalid status: {status}. Must be one of {valid_statuses}")

        self.status = status
        self.add_note(f"Status updated to: {status}")
