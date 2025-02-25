import chainlit as cl
from kubernetes import client, config
from kubernetes_cronjob_manager import create_cronjob
from openai import OpenAI
from orchestrator import Orchestrator


config.load_kube_config()

# Global configuration storage for the current job
job_config = {}

orchestrator = Orchestrator()

@cl.on_chat_start
async def on_chat_start():
    await cl.Message(
        content="""
        Welcome to OrchestrAI! Please enter your composite query.\n\nFor example: 
        Send me bible scripture that will help me with how I want to grow from my latest journaling in Notion.
        """
    ).send()

@cl.on_message
async def main(message):
    global job_config

    # Step 1: Capture the user's initial query.
    if "query" not in job_config:
        job_config["query"] = message.content.strip()

        #ai_response = orchestrator.determine_agents(message.content)
        #agents = ai_response.agents
        agents = ["notionfetchagent", "scripturegenerationagent", "notificationagent"]

        ui_response = cl.Message("<do the agent stuff here>")
        # if len(agents) > 0:
        #     ui_response = cl.Message(content=f"Looks like we have some agents we'll use for this! {', '.join(agents)}")
        # else:
        #     ui_response = cl.Message(content=f"Uh oh! {ai_response.message} Please ask for something else!")
        await ui_response.send()

        # TODO: render a dropdown for choosing frequency of the job, and a submit button
        # When submit is pressed, call initialize_agents then build_and_render_ai_job_workflow
        agents = orchestrator.initialize_agents(message.content, agents)
        orchestrator.build_and_render_ai_job_workflow(agents, output_file_path="test.py")

    # else:
    #     #await cl.Message(message.content).send()
    #     await cl.Message("Sending cronjob!").send()

    #     cronjob_manifest = {
    #         "apiVersion": "batch/v1",
    #         "kind": "CronJob",
    #         "metadata": {
    #             "name": "my-cronjob"
    #         },
    #         "spec": {
    #             "schedule": "* * * * *",  # Runs every minute
    #             "concurrencyPolicy": "Forbid",
    #             "successfulJobsHistoryLimit": 1,
    #             "failedJobsHistoryLimit": 1,
    #             "jobTemplate": {
    #                 "spec": {
    #                     "template": {
    #                         "spec": {
    #                             "containers": [
    #                                 {
    #                                     "name": "hello-world",
    #                                     "image": "python:3.12-slim",
    #                                     "command": ["python", "/scripts/dummy.py"],
    #                                     "volumeMounts": [
    #                                         {
    #                                             "name": "python-scripts",
    #                                             "mountPath": "/scripts/dummy.py"
    #                                         }
    #                                     ]
    #                                 }
    #                             ],
    #                             "restartPolicy": "OnFailure",
    #                             "volumes": [
    #                                 {
    #                                     "name": "python-scripts",
    #                                     "hostPath": {
    #                                         "path": "/Users/deanorenstein/Documents/academic/coding_stuff/OrchestrAI/s3_storage/dean/dummy.py",
    #                                         "type": "File"
    #                                     }
    #                                 }
    #                             ]
    #                         }
    #                     }
    #                 }
    #             }
    #         }
    #     }
        
    #     batch_v1 = client.BatchV1Api()
    #     response = batch_v1.create_namespaced_cron_job(
    #         namespace="default",  # Adjust if using a different namespace
    #         body=cronjob_manifest
    #     )

    #     await cl.Message("Done!").send()