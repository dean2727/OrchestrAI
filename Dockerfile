FROM python:3.12-slim

WORKDIR /app

COPY s3_storage/requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

# Default command starts the Chainlit UI.
# For scheduled jobs, the CronJob spec will override the command.
CMD ["python", "-m", "chainlit", "run"]