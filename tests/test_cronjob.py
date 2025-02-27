from kubernetes import client, config
import os

cron_schedule = "* * * * *"
job_id = f"job-abc-xyz"
username = "dean"
# os.path.abspath('.')
home_abs_path = "/Users/deanorenstein/Documents/academic/coding_stuff/OrchestrAI"
s3_path = f"s3_storage/{username}"
job_file_name = "job1.py"
template_save_path = f"{home_abs_path}/{s3_path}/{job_file_name}"
tools_path = f"{home_abs_path}/tools/"
image = "ai-job:latest"
user_notion_db_id = "9dd35093a917436f9de6aa56b28c6182"

cronjob_manifest = {
    "apiVersion": "batch/v1",
    "kind": "CronJob",
    "metadata": {
        "name": f"{job_id}",
        "namespace": "default"
    },
    "spec": {
        "schedule": f"{cron_schedule}",  # Runs every minute
        "concurrencyPolicy": "Forbid",
        "successfulJobsHistoryLimit": 1,
        "failedJobsHistoryLimit": 1,
        "jobTemplate": {
            "spec": {
                "template": {
                    "spec": {
                        "containers": [
                            {
                                "name": "hello-world",
                                "image": f"{image}",
                                "command": ["python", "graph.py"],
                                "env": [
                                    {"name": "NOTION_DB_ID", "value": user_notion_db_id},
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

batch_v1 = client.BatchV1Api()
response = batch_v1.create_namespaced_cron_job(
    namespace="default",  # Adjust if using a different namespace
    body=cronjob_manifest
)