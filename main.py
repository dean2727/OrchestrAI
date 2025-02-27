import chainlit as cl
from kubernetes import config
from kubernetes_cronjob_manager import create_cronjob
from openai import OpenAI
from orchestrator.orchestrator import Orchestrator
from chainlit.input_widget import Select, TextInput
from datetime import datetime
import os
import re

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

# Global configuration storage for the current job
job_config = {}

# Orchestrator agent
orchestrator = Orchestrator()

# cronjob vars
home_abs_path = os.path.abspath('.')
tools_path = f"{home_abs_path}/tools/"
image = "ai-job:latest"
namespace = "default"

@cl.on_chat_start
async def on_chat_start():
    await cl.Message(
        content="""
        Welcome to OrchestrAI! Please enter your composite query.\n\nFor example: 
        Send me bible scripture that will help me with how I want to grow from my latest journaling in Notion.
        """
    ).send()
    # TODO: implement better design of scheduling jobs (start date, every x day/
    # week/hour, at a certain time)
    settings = await cl.ChatSettings(
    [
        Select(
            id="Model",
            label="AI Job Frequency",
            values=["Manual", "Every minute", "Every hour", "Every day", "Every week"],
            initial_index=0,
        ),
        TextInput(id="StartDate", label="AI Job Start Date (YYYY-MM-DD)", initial="2025-02-27"),
        TextInput(id="StartTime", label="AI Job Start Time (HH:MM)", initial="00:00"),
        TextInput(id="NotionDBID", label="Notion Database ID ()", initial="123")
    ]).send()
    
    frequency = settings["Model"]
    start_date = settings["StartDate"]
    start_time = settings["StartTime"]

    # Store validated settings in user session
    cl.user_session.set("frequency", frequency)
    cl.user_session.set("start_date", start_date)
    cl.user_session.set("start_time", start_time)
    cl.user_session.set("notion_db_id", "123")

@cl.on_settings_update
async def on_settings_update(settings):
    # Validate and update settings
    frequency = settings["Model"]
    start_date = settings["StartDate"]
    start_time = settings["StartTime"]
    notion_db_id = settings["NotionDBID"]

    # Validate StartDate
    if not validate_date(start_date):
        await cl.Message(content="Invalid Start Date format. Expected YYYY-MM-DD. Keeping previous value.").send()
        start_date = cl.user_session.get("start_date", "2025-02-27")  # Fallback to previous or default

    # Validate StartTime
    if not validate_time(start_time):
        await cl.Message(content="Invalid Start Time format. Expected HH:MM. Keeping previous value.").send()
        start_time = cl.user_session.get("start_time", "00:00")  # Fallback to previous or default

    # Update validated settings in user session
    cl.user_session.set("frequency", frequency)
    cl.user_session.set("start_date", start_date)
    cl.user_session.set("start_time", start_time)
    cl.user_session.set("notion_db_id", notion_db_id)
    await cl.Message(content=f"Settings updated: Frequency={frequency}, Start Date={start_date}, Start Time={start_time}").send()

@cl.on_message
async def main(message):
    global job_config

    # Retrieve settings from user session
    frequency = cl.user_session.get("frequency", "Manual")
    start_date = cl.user_session.get("start_date", "2025-02-27")
    start_time = cl.user_session.get("start_time", "00:00")
    notion_db_id = cl.user_session.get("notion_db_id", "")

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

    job_id = f"job-{cl.context.session_id}-{hash(message.content)}"

    # TODO: get dynamically
    username = "dean"
    s3_path = f"s3_storage/{username}/"

    # Check path, increment
    pattern = r"job(\d+)\.py"
    s3_path_files = os.listdir(s3_path)
    job_numbers = [int(match.group(1)) for f in s3_path_files if (match := re.match(pattern, f))]
    new_number = max(job_numbers, default=0) + 1
    job_file_name = f"job{new_number}.py"
    template_save_path = f"{home_abs_path}/{s3_path}/{job_file_name}"

    async def local_job_function():
        result = f"Processed query: '{message.content}' with frequency: {frequency}"
        await cl.Message(content=result).send()

    if "query" not in job_config and cron_schedule:
        job_config["query"] = message.content.strip()

        # Determine the agents
        #ai_response = orchestrator.determine_agents(message.content)
        #agents = ai_response.agents
        agents = ["notionfetchagent", "scripturegenerationagent", "notificationagent"]

        # Initialize agents (determine template vars)
        #agents = orchestrator.initialize_agents(message.content, agents)
        # Render the workflow (python file)
        #orchestrator.build_and_render_ai_job_workflow(agents, output_file_path=job_file_name)

        cronjob_manifest = {
            "apiVersion": "batch/v1",
            "kind": "CronJob",
            "metadata": {
                "name": f"{job_id}",
                "namespace": f"{namespace}"
            },
            "spec": {
                "schedule": f"{cron_schedule}",
                "concurrencyPolicy": "Forbid",
                "successfulJobsHistoryLimit": 1,
                "failedJobsHistoryLimit": 1,
                "jobTemplate": {
                    "spec": {
                        "template": {
                            "spec": {
                                "containers": [
                                    {
                                        "name": f"{username}-{job_file_name[:-3]}",
                                        "image": f"{image}",
                                        "command": ["python", "graph.py"],
                                        "env": [
                                            {"name": "NOTION_DB_ID", "value": notion_db_id },
                                            {"name": "NOTION_BEARER_TOKEN", "value": os.environ["NOTION_BEARER_TOKEN"]},
                                            {"name": "OPENAI_API_KEY", "value": os.environ["OPENAI_API_KEY"]},
                                        ],
                                        "volumeMounts": [
                                            {
                                                "name": "ai-job-template",
                                                "mountPath": "graph.py"
                                            }
                                        ]
                                    }
                                ],
                                "restartPolicy": "OnFailure",
                                "volumes": [
                                    {
                                        "name": "ai-job-template",
                                        "hostPath": {
                                            "path": f"{template_save_path}",
                                            "type": "File"
                                        }
                                    }
                                ]
                            }
                        }
                    }
                }
            }
        }

        orchestrator.submit_cronjob(namespace, cronjob_manifest)

        await cl.Message("Job submitted!").send()