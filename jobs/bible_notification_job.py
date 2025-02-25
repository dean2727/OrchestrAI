import os
import openai
from twilio.rest import Client
from .abstract_job import AIJob

class BibleNotificationJob(AIJob):
    def __init__(self, phone_number, concept):
        self.phone_number = phone_number
        self.concept = concept
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required.")
        openai.api_key = self.openai_api_key

        self.twilio_account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.twilio_auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.twilio_from_number = os.getenv("TWILIO_FROM_NUMBER")

    def run(self):
        # Build the prompt for generating Bible scripture
        prompt = (
            f"Generate a Bible scripture that relates to the concept '{self.concept}'. "
            "Please include appropriate Bible verses and references in your answer."
        )
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that generates Bible scriptures."},
                {"role": "user", "content": prompt}
            ]
        )
        scripture = response.choices[0].message.content.strip()

        # Send the generated scripture via Twilio SMS
        # client = Client(self.twilio_account_sid, self.twilio_auth_token)
        # message = client.messages.create(
        #     body=scripture,
        #     from_=self.twilio_from_number,
        #     to=self.phone_number
        # )
        #print(f"Sent message SID: {message.sid}")
        print("Sent!")

    def get_command(self):
        return "python -m jobs.bible_notification_job_runner"

    def get_job_name(self):
        return "bible-notification-job"