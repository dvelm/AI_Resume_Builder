import os
import json
import datetime
from typing import List, Dict, Any, Optional
from dataclasses import asdict, is_dataclass

from src.job import Job
from src.job_application import JobApplication
from src.logging import logger
from config import JOB_APPLICATIONS_DIR


class JobApplicationEncoder(json.JSONEncoder):
    """Custom JSON encoder for Job and JobApplication objects"""
    def default(self, obj):
        if is_dataclass(obj):
            return asdict(obj)
        elif isinstance(obj, datetime.datetime):
            return obj.isoformat()
        return super().default(obj)


class JobApplicationTracker:
    """Tracks job applications and their status"""

    def __init__(self, db_file: str = "job_applications_db.json"):
        """Initialize the tracker with database file"""
        # Ensure applications directory exists
        os.makedirs(JOB_APPLICATIONS_DIR, exist_ok=True)

        self.db_file = os.path.join(JOB_APPLICATIONS_DIR, db_file)
        self.applications = self._load_applications()

    def _load_applications(self) -> Dict[str, Dict[str, Any]]:
        """Load applications from database file"""
        if not os.path.exists(self.db_file):
            return {}

        try:
            with open(self.db_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error loading applications database: {e}")
            return {}

    def _save_applications(self) -> None:
        """Save applications to database file"""
        try:
            with open(self.db_file, 'w') as f:
                json.dump(self.applications, f, cls=JobApplicationEncoder, indent=2)
        except IOError as e:
            logger.error(f"Error saving applications database: {e}")

    def add_application(self, job_application: JobApplication, status: str = "applied") -> None:
        """Add a new job application to the tracker"""
        job = job_application.job

        if not job.id:
            # Generate an ID if not present
            from uuid import uuid4
            job.id = str(uuid4())

        # Create application entry
        application_entry = {
            "job": asdict(job),
            "application_date": datetime.datetime.now().isoformat(),
            "status": status,
            "resume_path": job_application.resume_path,
            "cover_letter_path": job_application.cover_letter_path,
            "follow_up_date": None,
            "notes": []
        }

        self.applications[job.id] = application_entry
        self._save_applications()
        logger.info(f"Added application for {job.role} at {job.company}")

    def update_status(self, job_id: str, status: str) -> bool:
        """Update the status of an application"""
        if job_id not in self.applications:
            logger.error(f"Application with ID {job_id} not found")
            return False

        self.applications[job_id]["status"] = status
        self.applications[job_id]["last_updated"] = datetime.datetime.now().isoformat()

        if status == "interview_scheduled":
            # Add placeholder for interview date
            self.applications[job_id]["interview_date"] = None

        self._save_applications()
        logger.info(f"Updated application {job_id} status to {status}")
        return True

    def add_note(self, job_id: str, note: str) -> bool:
        """Add a note to an application"""
        if job_id not in self.applications:
            logger.error(f"Application with ID {job_id} not found")
            return False

        note_entry = {
            "date": datetime.datetime.now().isoformat(),
            "text": note
        }

        self.applications[job_id]["notes"].append(note_entry)
        self._save_applications()
        return True

    def set_follow_up_date(self, job_id: str, follow_up_date: datetime.datetime) -> bool:
        """Set a follow-up date for an application"""
        if job_id not in self.applications:
            logger.error(f"Application with ID {job_id} not found")
            return False

        self.applications[job_id]["follow_up_date"] = follow_up_date.isoformat()
        self._save_applications()
        return True

    def get_application(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific application by ID"""
        return self.applications.get(job_id)

    def get_all_applications(self) -> List[Dict[str, Any]]:
        """Get all applications"""
        return [
            {"id": job_id, **app_data}
            for job_id, app_data in self.applications.items()
        ]

    def get_applications_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Get applications filtered by status"""
        return [
            {"id": job_id, **app_data}
            for job_id, app_data in self.applications.items()
            if app_data["status"] == status
        ]

    def get_applications_needing_follow_up(self) -> List[Dict[str, Any]]:
        """Get applications that need follow-up today"""
        today = datetime.datetime.now().date()

        return [
            {"id": job_id, **app_data}
            for job_id, app_data in self.applications.items()
            if app_data.get("follow_up_date") and
               datetime.datetime.fromisoformat(app_data["follow_up_date"]).date() <= today
        ]

    def get_application_statistics(self) -> Dict[str, Any]:
        """Get statistics about applications"""
        status_counts = {}
        company_counts = {}
        applications_by_month = {}

        for app_data in self.applications.values():
            # Count by status
            status = app_data["status"]
            status_counts[status] = status_counts.get(status, 0) + 1

            # Count by company
            company = app_data["job"]["company"]
            company_counts[company] = company_counts.get(company, 0) + 1

            # Count by month
            app_date = datetime.datetime.fromisoformat(app_data["application_date"])
            month_key = f"{app_date.year}-{app_date.month:02d}"
            applications_by_month[month_key] = applications_by_month.get(month_key, 0) + 1

        return {
            "total_applications": len(self.applications),
            "status_counts": status_counts,
            "top_companies": sorted(company_counts.items(), key=lambda x: x[1], reverse=True)[:5],
            "applications_by_month": applications_by_month
        }
