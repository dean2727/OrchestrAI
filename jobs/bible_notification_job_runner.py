import os
from bible_notification_job import BibleNotificationJob

def main():
    phone_number = os.getenv("PHONE_NUMBER")
    concept = "faith"
    if not phone_number:
        raise ValueError("PHONE_NUMBER environment variable is required.")
    job = BibleNotificationJob(phone_number, concept)
    job.run()

if __name__ == "__main__":
    main()