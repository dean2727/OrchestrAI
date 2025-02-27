# Docker image for a scheduled cronjob
FROM python:3.12-slim

WORKDIR /scripts

COPY orchestrator/requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY tools/ .

CMD ["python", "graph.py"]