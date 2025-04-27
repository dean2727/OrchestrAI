import chainlit as cl
from kubernetes import config
from openai import OpenAI
from orchestrator.orchestrator import Orchestrator
from chainlit.input_widget import Select, TextInput
from datetime import datetime
import os
import re
import tempfile
from google.cloud import storage
from google.api_core.exceptions import NotFound, Forbidden
import subprocess

config.load_kube_config()

def validate_date(date_str: str) -> bool:
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False

def validate_time(time_str: str) -> bool:
    try:
        datetime.strptime(time_str, "%H:%M")
        return True
    except ValueError:
        return False

def validate_phone_number(phone_number: str) -> bool:
    phone_pattern = re.compile(r'^\+\d{1,3}\d{3,14}$')
    return bool(phone_pattern.match(phone_number))

def validate_email(email: str) -> bool:
    email_pattern = re.compile(r'^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}$')
    return bool(email_pattern.match(email))

# Global configuration storage for the current job
job_config = {}

# Orchestrator agent
orchestrator = Orchestrator()

# cronjob vars
home_abs_path = os.path.abspath('.')
tools_path = f"{home_abs_path}/tools/"
# image = "dean27/orchestrai:latest"
# namespace = "default"
gcs_bucket_name = "all-ai-jobs"
gc_region = "us-central1"

@cl.on_chat_start
async def on_chat_start():
    await cl.Message(
        content="""
        Welcome to OrchestrAI! Please enter your composite query.\n\nFor example: 
        Send me bible scripture that will help me with how I want to grow from my latest journaling in Notion.
        """
    ).send()
    settings = await cl.ChatSettings(
    [
        Select(
            id="Model",
            label="AI Job Frequency",
            values=["Manual", "Every minute", "Every hour", "Every day", "Every week"],
            initial_index=1,
        ),
        TextInput(id="StartDate", label="AI Job Start Date (YYYY-MM-DD)", initial=datetime.now().strftime("%Y-%m-%d")),
        TextInput(id="StartTime", label="AI Job Start Time (HH:MM)", initial=datetime.now().strftime("%H:%M")),
        TextInput(id="NotionDBID", label="Notion Database ID (https://www.notion.so/myworkspace/<ID HERE>)", initial="9dd35093a917436f9de6aa56b28c6182"),
        TextInput(id="PhoneNumber", label="Phone Number (E.164 Format)", initial="+13045492645"),
        TextInput(id="Email", label="Email Address", initial="dto3576@gmail.com")
    ]).send()
    
    frequency = settings["Model"]
    start_date = settings["StartDate"]
    start_time = settings["StartTime"]
    notion_db_id = settings["NotionDBID"]
    phone_number = settings["PhoneNumber"]
    email = settings["Email"]

    # Store validated settings in user session
    cl.user_session.set("frequency", frequency)
    cl.user_session.set("start_date", start_date)
    cl.user_session.set("start_time", start_time)
    cl.user_session.set("notion_db_id", notion_db_id)
    cl.user_session.set("phone_number", phone_number)
    cl.user_session.set("email", email)

@cl.on_settings_update
async def on_settings_update(settings):
    # Validate and update settings
    frequency = settings["Model"]
    start_date = settings["StartDate"]
    start_time = settings["StartTime"]
    notion_db_id = settings["NotionDBID"]
    phone_number = settings["PhoneNumber"]
    email = settings["Email"]

    # Validate StartDate
    if not validate_date(start_date):
        await cl.Message(content="Invalid Start Date format. Expected YYYY-MM-DD. Keeping previous value.").send()
        start_date = cl.user_session.get("start_date", "2025-02-27")  # Fallback to previous or default

    # Validate StartTime
    if not validate_time(start_time):
        await cl.Message(content="Invalid Start Time format. Expected HH:MM. Keeping previous value.").send()
        start_time = cl.user_session.get("start_time", "00:00")  # Fallback to previous or default

    # Validate PhoneNumber
    if not validate_phone_number(phone_number):
        await cl.Message(content="Invalid Phone Number format. Expected E.164 Format. Keeping previous value.").send()
        phone_number = cl.user_session.get("phone_number", "+1234567890")  # Fallback to previous or default

    # Validate Email
    if not validate_email(email):
        await cl.Message(content="Invalid Email format. Keeping previous value.").send()
        email = cl.user_session.get("email", "example@example.com")  # Fallback to previous or default

    # Update validated settings in user session
    cl.user_session.set("frequency", frequency)
    cl.user_session.set("start_date", start_date)
    cl.user_session.set("start_time", start_time)
    cl.user_session.set("notion_db_id", notion_db_id)
    cl.user_session.set("phone_number", phone_number)
    cl.user_session.set("email", email)
    await cl.Message(content=f"Settings updated: Frequency={frequency}, Start Date={start_date}, Start Time={start_time}, Phone Number={phone_number}, Email={email}").send()

@cl.on_message
async def main(message):
    global job_config

    # Retrieve settings from user session
    frequency = cl.user_session.get("frequency", "Manual")
    start_date = cl.user_session.get("start_date", "2025-02-27")
    start_time = cl.user_session.get("start_time", "00:00")
    notion_db_id = cl.user_session.get("notion_db_id", "")
    phone_number = cl.user_session.get("phone_number", "+1234567890")
    email = cl.user_session.get("email", "example@example.com")

    # Validate and combine start date and time
    try:
        start_datetime = datetime.strptime(f"{start_date} {start_time}", "%Y-%m-%d %H:%M")
    except ValueError:
        await cl.Message(content="Invalid start date/time format. Using current time as fallback.").send()
        start_datetime = datetime.now()

    # Map Chainlit frequency to Kubernetes cron schedule
    frequency_map = {
        "Manual": None,  # Won’t create a CronJob, runs once locally
        "Every minute": "* * * * *",
        "Every hour": "0 * * * *",
        "Every day": f"{start_datetime.minute} {start_datetime.hour} * * *",
        "Every week": f"{start_datetime.minute} {start_datetime.hour} * * {start_datetime.weekday()}"
    }

    cron_schedule = frequency_map.get(frequency)
        

    if "query" not in job_config and cron_schedule:
        job_config["query"] = message.content.strip()

        # Determine the agents
        ai_response = orchestrator.determine_agents(message.content)
        #print("DEBUG:", ai_response)
        agents = ai_response.agents
        #agents = ["notionfetchagent", "generationagent", "notificationagent"]

        await cl.Message(content=f"Going to use these agents: {agents}").send()

        # Initialize agents (determine template vars)
        agents = orchestrator.initialize_agents(message.content, agents)
        # Render the workflow (python file)
        rendered_template = orchestrator.build_and_render_ai_job_workflow(agents)

        # cronjob_manifest = {
        #     "apiVersion": "batch/v1",
        #     "kind": "CronJob",
        #     "metadata": {
        #         "name": f"{job_id}",
        #         "namespace": f"{namespace}"
        #     },
        #     "spec": {
        #         "schedule": f"{cron_schedule}",
        #         "concurrencyPolicy": "Forbid",
        #         "successfulJobsHistoryLimit": 1,
        #         "failedJobsHistoryLimit": 1,
        #         "jobTemplate": {
        #             "spec": {
        #                 "template": {
        #                     "spec": {
        #                         "containers": [
        #                             {
        #                                 "name": f"{username}-{job_file_name[:-3]}",
        #                                 "image": f"{image}",
        #                                 "command": ["python", "graph.py"],
        #                                 "env": [
        #                                     {"name": "NOTION_DB_ID", "value": notion_db_id },
        #                                     {"name": "NOTION_BEARER_TOKEN", "value": os.environ["NOTION_BEARER_TOKEN"]},
        #                                     {"name": "OPENAI_API_KEY", "value": os.environ["OPENAI_API_KEY"]},
        #                                     {"name": "USER_PHONE_NUMBER", "value": phone_number},
        #                                     {"name": "USER_EMAIL", "value": email},
        #                                 ],
        #                                 "volumeMounts": [
        #                                     {
        #                                         "name": "ai-job-template",
        #                                         "mountPath": "/scripts/graph.py"
        #                                     }
        #                                 ]
        #                             }
        #                         ],
        #                         "restartPolicy": "OnFailure",
        #                         "volumes": [
        #                             {
        #                                 "name": "ai-job-template",
        #                                 "hostPath": {
        #                                     "path": f"{template_save_path}",
        #                                     "type": "File"
        #                                 }
        #                             }
        #                         ]
        #                     }
        #                 }
        #             }
        #         }
        #     }
        # }

        # orchestrator.submit_cronjob(namespace, cronjob_manifest)

        # Upload script to Google Cloud Storage, from temporary local storage
        with tempfile.TemporaryDirectory() as temp_dir:
            # Ask AI what 2 words describe the job
            ai_description = "Generate a script to describe the job"
            ai_response = OpenAI.generate_text(ai_description)
            job_description = ai_response.split()[:2]  # Extract the first two words from the response
            job_name = f"job-{job_description}"
            file_name = f"{job_name}.py"
            file_path = os.path.join(temp_dir, file_name)

            # Write the file to the temp path
            with open(file_path, 'w') as file:
                file.write("print('Hello, World!')")
                #file.write(rendered_template)
    
            # Upload script to Google Cloud Storage
            try:
                # Initialize GCS client
                client = storage.Client(project="orchestrai-456719")
                bucket = client.bucket(gcs_bucket_name)
                
                # Verify bucket exists
                bucket_exists = bucket.exists()
                if not bucket_exists:
                    raise ValueError(f"Bucket {gcs_bucket_name} does not exist")

                # Upload the script
                blob = bucket.blob(file_name)
                blob.upload_from_filename(file_path)
                print(f"Uploaded {file_path} to gs://{file_name}")
            except (NotFound, Forbidden, ValueError) as e:
                print(f"Failed to upload script to GCS: {str(e)}")
            except Exception as e:
                print(f"Unexpected error during GCS upload: {str(e)}")

        # Deploy the job to google cloud run
        project_id = os.environ["GC_PROJECT_ID"]
        deploy_cmd = [
            "gcloud", "run", "jobs", "deploy", job_name,
            "--source", ".",
            "--command", "bash",
            "--args", "-c",
            "--args", f"gsutil cp gs://{gcs_bucket_name}/{job_name}.py /app/scripts/ && python scripts/{job_name}.py",
            "--region", gc_region,
            "--project", project_id,
            "--set-env-vars", f"MESSAGE={message.content},FREQUENCY={frequency}",
            "--quiet"
        ]
        subprocess.run(deploy_cmd, check=True, capture_output=True, text=True)

        # Create Cloud Scheduler job
        schedule_cmd = [
            "gcloud", "scheduler", "jobs", "create", "http", f"schedule-{job_name}",
            "--schedule", cron_schedule,
            "--uri", f"https://run.googleapis.com/v1/projects/{project_id}/locations/{gc_region}/jobs/{job_name}:run",
            "--http-method", "POST",
            "--oidc-service-account-email", f"cloud-run-invoker@{project_id}.iam.gserviceaccount.com",
            "--location", gc_region,
            "--project", project_id,
            "--quiet"
        ]
        subprocess.run(schedule_cmd, check=True, capture_output=True, text=True)

        result = f"Processed query: '{message.content}' with frequency: {frequency}"
        await cl.Message(content=result).send()