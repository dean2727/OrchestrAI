from kubernetes import client, config
import uuid

def create_cronjob(job_name, schedule, image, command, env_vars=None):
    """
    Creates a Kubernetes CronJob in the default namespace.
    
    Parameters:
      - job_name: a unique identifier for the job (e.g., "bible-notification-job")
      - schedule: cron-formatted schedule string (e.g., "0 */2 * * *" for every 2 hours)
      - image: container image that includes this codebase
      - command: command to run inside the container (e.g., "python -m jobs.bible_notification_job_runner")
      - env_vars: dictionary of environment variables to pass to the container
    """

    # Load kubeconfig (this works with minikube)
    config.load_kube_config()

    batch_v1 = client.BatchV1Api()

    # Create a unique name for the CronJob
    cronjob_name = f"{job_name}-{uuid.uuid4().hex[:6]}"

    metadata = client.V1ObjectMeta(name=cronjob_name)

    # Prepare environment variables for the container
    env_list = []
    if env_vars:
        for key, value in env_vars.items():
            env_list.append(client.V1EnvVar(name=key, value=value))

    # Define the container spec
    container = client.V1Container(
        name=job_name,
        image=image,
        command=["/bin/sh", "-c", command],
        env=env_list,
    )

    # Define the Pod template
    template = client.V1PodTemplateSpec(
        metadata=client.V1ObjectMeta(labels={"job": job_name}),
        spec=client.V1PodSpec(restart_policy="OnFailure", containers=[container])
    )

    # Define the Job spec within the CronJob
    job_spec = client.V1JobSpec(template=template)

    # Define the CronJob spec
    cronjob_spec = client.V1CronJobSpec(
        schedule=schedule,
        job_template=client.V1JobTemplateSpec(spec=job_spec)
    )

    # Assemble the CronJob object
    cronjob = client.V1CronJob(
        api_version="batch/v1",
        kind="CronJob",
        metadata=metadata,
        spec=cronjob_spec
    )

    # Create the CronJob in the "default" namespace
    api_response = batch_v1.create_namespaced_cron_job(
        namespace="default",
        body=cronjob
    )
    print(f"CronJob created: {api_response.metadata.name}")
    return api_response.metadata.name