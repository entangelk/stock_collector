"""
Repository for job status operations.
"""
from typing import List, Optional
from datetime import date, datetime
import logging

from repositories.base import BaseRepository
from schemas import JobStatusRecord, JobStatus

logger = logging.getLogger(__name__)


class JobStatusRepository(BaseRepository):
    """Repository for managing job status records."""
    
    def __init__(self):
        super().__init__("system_info", "job_status")
    
    def create_job_id(self, date_kst: date, job_name: str) -> str:
        """Create standardized job ID."""
        date_str = date_kst.isoformat() if isinstance(date_kst, date) else date_kst
        return f"{date_str}_{job_name}"
    
    def start_job(self, job_name: str, date_kst: date) -> str:
        """Record job start."""
        job_id = self.create_job_id(date_kst, job_name)
        
        job_record = {
            "_id": job_id,
            "job_name": job_name,
            "date_kst": date_kst.isoformat() if isinstance(date_kst, date) else date_kst,
            "status": JobStatus.RUNNING.value,
            "start_time_utc": datetime.utcnow(),
            "end_time_utc": None,
            "error_message": None,
            "records_processed": None
        }
        
        try:
            # Use upsert to handle potential retries
            self.upsert({"_id": job_id}, job_record)
            logger.info(f"Started job: {job_id}")
            return job_id
        except Exception as e:
            logger.error(f"Failed to start job {job_id}: {e}")
            raise
    
    def complete_job(self, job_id: str, records_processed: Optional[int] = None) -> bool:
        """Mark job as completed."""
        update_data = {
            "status": JobStatus.COMPLETED.value,
            "end_time_utc": datetime.utcnow()
        }
        
        if records_processed is not None:
            update_data["records_processed"] = records_processed
        
        try:
            result = self.update_one({"_id": job_id}, update_data)
            if result:
                logger.info(f"Completed job: {job_id}")
            return result
        except Exception as e:
            logger.error(f"Failed to complete job {job_id}: {e}")
            return False
    
    def fail_job(self, job_id: str, error_message: str) -> bool:
        """Mark job as failed."""
        update_data = {
            "status": JobStatus.FAILED.value,
            "end_time_utc": datetime.utcnow(),
            "error_message": error_message
        }
        
        try:
            result = self.update_one({"_id": job_id}, update_data)
            if result:
                logger.error(f"Failed job: {job_id} - {error_message}")
            return result
        except Exception as e:
            logger.error(f"Failed to update failed job {job_id}: {e}")
            return False
    
    def get_job_status(self, job_name: str, date_kst: date) -> Optional[JobStatusRecord]:
        """Get job status for specific date."""
        job_id = self.create_job_id(date_kst, job_name)
        doc = self.find_one({"_id": job_id})
        if doc:
            return JobStatusRecord(**doc)
        return None
    
    def get_last_successful_job(self, job_name: str) -> Optional[JobStatusRecord]:
        """Get the last successful job of given type."""
        docs = self.find_many(
            {"job_name": job_name, "status": JobStatus.COMPLETED.value},
            sort=[("date_kst", -1)],
            limit=1
        )
        if docs:
            return JobStatusRecord(**docs[0])
        return None
    
    def get_last_successful_date(self, job_name: str) -> Optional[date]:
        """Get the date of the last successful job."""
        last_job = self.get_last_successful_job(job_name)
        if last_job:
            date_str = last_job.date_kst
            if isinstance(date_str, str):
                return date.fromisoformat(date_str)
            return date_str
        return None
    
    def get_failed_jobs(self, job_name: Optional[str] = None, 
                       days_back: int = 7) -> List[JobStatusRecord]:
        """Get failed jobs within specified days."""
        cutoff_date = datetime.utcnow().date()
        cutoff_date = date(cutoff_date.year, cutoff_date.month, cutoff_date.day - days_back)
        
        filter_dict = {
            "status": JobStatus.FAILED.value,
            "date_kst": {"$gte": cutoff_date.isoformat()}
        }
        
        if job_name:
            filter_dict["job_name"] = job_name
        
        docs = self.find_many(filter_dict, sort=[("date_kst", -1)])
        return [JobStatusRecord(**doc) for doc in docs]
    
    def get_running_jobs(self, job_name: Optional[str] = None) -> List[JobStatusRecord]:
        """Get currently running jobs."""
        filter_dict = {"status": JobStatus.RUNNING.value}
        if job_name:
            filter_dict["job_name"] = job_name
        
        docs = self.find_many(filter_dict, sort=[("start_time_utc", -1)])
        return [JobStatusRecord(**doc) for doc in docs]
    
    def get_job_history(self, job_name: str, limit: int = 30) -> List[JobStatusRecord]:
        """Get job history for specific job type."""
        docs = self.find_many(
            {"job_name": job_name},
            sort=[("date_kst", -1)],
            limit=limit
        )
        return [JobStatusRecord(**docs) for doc in docs]
    
    def cleanup_old_records(self, days_to_keep: int = 90) -> int:
        """Clean up old job status records."""
        cutoff_date = datetime.utcnow().date()
        cutoff_date = date(cutoff_date.year, cutoff_date.month, cutoff_date.day - days_to_keep)
        
        try:
            deleted_count = self.delete_many({
                "date_kst": {"$lt": cutoff_date.isoformat()}
            })
            logger.info(f"Cleaned up {deleted_count} old job status records")
            return deleted_count
        except Exception as e:
            logger.error(f"Failed to cleanup old records: {e}")
            return 0
    
    def get_job_statistics(self, job_name: Optional[str] = None, 
                          days_back: int = 30) -> dict:
        """Get job execution statistics."""
        cutoff_date = datetime.utcnow().date()
        cutoff_date = date(cutoff_date.year, cutoff_date.month, cutoff_date.day - days_back)
        
        filter_dict = {"date_kst": {"$gte": cutoff_date.isoformat()}}
        if job_name:
            filter_dict["job_name"] = job_name
        
        # Aggregate statistics
        pipeline = [
            {"$match": filter_dict},
            {"$group": {
                "_id": "$status",
                "count": {"$sum": 1},
                "avg_duration": {
                    "$avg": {
                        "$subtract": ["$end_time_utc", "$start_time_utc"]
                    }
                }
            }}
        ]
        
        stats = list(self.collection.aggregate(pipeline))
        
        result = {
            "total_jobs": sum(stat["count"] for stat in stats),
            "by_status": {stat["_id"]: stat["count"] for stat in stats}
        }
        
        # Add success rate
        completed_count = result["by_status"].get(JobStatus.COMPLETED.value, 0)
        total_finished = completed_count + result["by_status"].get(JobStatus.FAILED.value, 0)
        
        if total_finished > 0:
            result["success_rate"] = completed_count / total_finished
        else:
            result["success_rate"] = 0.0
        
        return result