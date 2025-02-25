from jobs.bible_notification_job import BibleNotificationJob

def get_job(job_type, **kwargs):
    """
    Returns an instance of an AIJob based on the job_type.
    Extend this function with additional job types as needed.
    """
    if job_type == "bible_notification":
        return BibleNotificationJob(kwargs.get("phone_number"), kwargs.get("concept"))
    raise ValueError(f"Unknown job type: {job_type}")