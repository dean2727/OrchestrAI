#!/bin/bash
# This script depicts what commands we need to run for Google Cloud Run: deploy job -> schedule the job
# We run said commands for each job spun up by OrchestrAI
# In here, we simply test it on a simple print script (job1), and a more realistic LangGraph flow (job2)

PROJECT_ID=$(cat .env | grep GC_PROJECT_ID | cut -d'=' -f2)
REGION="us-central1"
SCRIPT_DIR="tests"
SERVICE_ACCOUNT=$(cat .env | grep GC_SERVICE_ACCOUNT | cut -d'=' -f2)

# Deploy and schedule each job
for script in "$SCRIPT_DIR"/dummy_jobs/*; do
  if [[ -f "$script" ]]; then
    job_name=$(basename "$script" .py)  # e.g., job1
    #schedule="${schedules[$job_name]:-0 0 * * *}"  # Default to daily if not specified
    schedule="* * * * *"

    # Deploy the Cloud Run job
    gcloud run jobs deploy "$job_name" \
      --source . \
      --command python \
      --args "$script" \
      --region "$REGION" \
      --project "$PROJECT_ID" \
      --set-env-vars "MESSAGE=Run $job_name,FREQUENCY=$schedule" \
      --quiet

    gcloud run jobs add-iam-policy-binding job1 \
    --region us-central1 \
    --member=serviceAccount:$SERVICE_ACCOUNT \
    --role=roles/run.invoker

    gcloud scheduler jobs create http job1 \
      --location "$REGION" \
      --schedule "$schedule" \
      --uri="https://$REGION-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/$PROJECT_ID/jobs/job1:run" \
      --http-method POST \
      --oidc-service-account-email "$SERVICE_ACCOUNT" \
    # gcloud scheduler jobs create http job1 --location us-central1 --schedule "* * * * *" --uri="https://us-central1-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/orchestrai-456719/jobs/job1:run" --http-method POST --oidc-service-account-email oai-448@orchestrai-456719.iam.gserviceaccount.com
    

    # Notes:
    # gcloud run jobs get-iam-policy job1 \
# >     --region us-central1 \
# >     --project orchestrai-456719
    # gave output of "etag: ACAB"
    # But then we did: gcloud run jobs add-iam-policy-binding job1 \
# >     --region us-central1 \
# >     --member=serviceAccount:$SERVICE_ACCOUNT \
# >     --role=roles/run.invoker
    # And after running again, we got: 
#     bindings:
    # - members:
    #   - serviceAccount:$SERVICE_ACCOUNT
    #   role: roles/run.invoker
    # etag: BwYytCUp3zQ=
    # version: 1
  fi
done