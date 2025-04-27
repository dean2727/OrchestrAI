## What is OrchestrAI?

OrchestrAI is an AI job orchestrator to conveniently automate your everyday repetitive or tedious tasks. Through a simple chat interface, all you need to do is enter your query, choose the job parameters, and submit, and then a Kubernetes cronjob will be spun up for you, where AI agents will coordinate together to do what you asked at the set time interval. OrchestrAI is here to serve you, to radically simplify your life, and to open you up to bigger and better things.

## What can it do?

Here are the different kinds of jobs you can ask OrchestrAI to do:


Job Templates Based on Common Queries

To maximize usability, you can group similar user queries into predefined AI job templates, making it easy for users to create automations without manually defining every parameter. These templates serve as reusable blueprints for common use cases.

1. Notification & Reminder Jobs

💡 Purpose: Send periodic messages (e.g., Bible verses, motivational quotes, habit reminders).

📌 Example Queries:
	•	“Send me a Bible verse about strength every morning at 8 AM.”
	•	“Remind me of my personal goals every Sunday night.”
	•	“Give me a motivational quote every morning at 6 AM.”

2. Content Summarization Jobs

💡 Purpose: Automatically summarize and deliver key insights from long-form content (emails, notes, meetings, articles).

📌 Example Queries:
	•	“Summarize my emails and send them to me every morning.”
	•	“Summarize my Notion journal every evening and email it to me.”
	•	“Give me a one-paragraph summary of every article I save to my reading list.”

3. AI-Generated Insights Jobs

💡 Purpose: Provide AI-driven analysis or reflections on trends, personal data, or habits.

📌 Example Queries:
	•	“Analyze my meeting notes and highlight the key action items.”
	•	“What were my most discussed themes in my journal this month?”
	•	“Summarize trending AI research papers for me every week.”

4. AI-Powered Scheduling Jobs

💡 Purpose: Help users plan, schedule, and optimize their time using AI recommendations.

📌 Example Queries:
	•	“Remind me to check my budget on the 1st of every month.”
	•	“Analyze my work calendar and suggest blocks of time for deep work.”
	•	“Plan my workouts based on my weekly availability.”

🛠 AI Job Template:
	•	Inputs:
	•	User’s calendar data (Google Calendar, Notion).
	•	Scheduling preferences (morning/evening, weekdays/weekends).
	•	Duration of tasks (15 min, 30 min, 1 hour).
	•	Example Output:
	•	“🔔 Deep Work Block Scheduled: Based on your calendar, 2 hours of deep work has been scheduled for Wednesday at 9 AM.”

5. Automated Research & Tracking Jobs

💡 Purpose: Fetch, filter, and deliver real-time updates or research summaries.

📌 Example Queries:
	•	“Send me the latest AI research papers every Monday.”
	•	“Alert me when a new update is published on OpenAI’s blog.”
	•	“Track my reading progress and suggest my next book.”

6. Workflow & Integration Jobs

💡 Purpose: Automate interactions between different apps (Notion, Google Drive, Slack, email).

📌 Example Queries:
	•	“Whenever I add a new task in Notion, create a Google Calendar event for it.”
	•	“If I receive a high-priority email, summarize it and notify me via SMS.”
	•	“Every week, extract my completed tasks and generate a progress report.”

7. Personal Development & Coaching Jobs

💡 Purpose: AI-guided coaching and self-improvement tracking.

📌 Example Queries:
	•	“Help me build a daily habit of reading the Bible.”
	•	“Track my emotional well-being based on my daily journal.”
	•	“Suggest a new book based on my reading history.”


GCloud Run Commands:

List Cloud Scheduler Jobs (schedules):

```bash
gcloud scheduler jobs list --project <project id>
```

List Cloud Run Jobs:

```bash
gcloud run jobs list --region us-central1 --project <project ID>
```

List Runs for a Job:

```bash
gcloud run jobs executions list --job job1 --region us-central1 --project <project ID>
```

View Logs:

```bash
gcloud logging read "resource.type=cloud_run_job resource.labels.job_name=job1" --project <project ID>
```

Run a job, logged in as dto:

```bash
curl -H "Authorization: Bearer $(gcloud auth print-access-token)" https://us-central1-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/orchestrai-456719/jobs/job1
```

## Rearchitecting towards MCP (model context protocol), Google ADK (agent development kit), and A2A protocol (agent2agent)

Rather than an orchestrator/meta agent determine the flow between a select set of agents in a pool of agents, and giving "template variable values" for inserted LangGraph code, which involves a lot of code complexity, due to all of the combinations, and is ultimately not that clean, extendable, or reliable, we can make use of more modern techniques with MCP and A2A.

MCP would enable a given agent to "discover" all kinds of data sources/connectors, if it must reach out to get more context on something.

A2A would enables agents to discover each other amongst the pool, delegating tasks, rather than relying on a "supervisory agent that tells all of them what to do".

Using the Google ADK allows us to use 1 single cloud provider - the one being used for the recurring kubernetes job executions (Cloud Run) - is cleaner code, more unified and simple, and offers all of the kinds of functionality that OrchestrAI requires. In the docs, there is a mentioning when building an agent team that there is a "root agent" (or orchestrator), that receives the initial user request, and which delegates the request to the most appropraite specialized sub-agent based on the user's intent. A direct mapping from the older orchestrator agent I did here in this project.

The possilbe Google ADK agents we can create are:

| Type                     | Purpose                                                                 | Mapping from README Queries                                                                 | ADK Role / Vertex AI Interaction                                                                                     |
|--------------------------|-------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------|
| **Notification Agent**   | Send scheduled or triggered notifications to the user.                  | Notification & Reminder Jobs (e.g., "Send me a Bible verse ...", "Remind me of my personal goals...") | Receives messages with content and recipient details. Uses backend services (SMS, email). Minimal Vertex AI unless content needs real-time generation. |
| **Content Fetch Agent**  | Retrieve content from various external sources (Notion, email, web).   | Content Summarization Jobs, Automatic Research & Tracking Jobs, Workflow & Integration Jobs (e.g., "Summarize my emails", "Fetch latest AI papers") | Contains logic/tools for API interaction (Notion, Gmail, web). Sends fetched content via Agent2Agent. Minor Vertex AI for parsing/validation if needed. |
| **Summarization Agent**  | Generate concise summaries of provided text content.                    | Content Summarization Jobs (e.g., "Summarize my emails", "Summarize my Notion journal", "Summarize every article") | Receives raw text via Agent2Agent. Heavily uses Vertex AI text generation models (Gemini) for summarization. Sends summary to agent. |
| **Analysis/Reasoning Agent** | Perform deeper analysis, extract insights, or apply reasoning to data. | AI-Generated Insights Jobs, AI-Powered Scheduling Jobs, Personal Development & Coaching Jobs (e.g., "Analyze meeting notes", "Most discussed themes", "Track emotional well-being") | Receives data/text via Agent2Agent. Heavily uses Vertex AI models (potentially advanced/fine-tuned) for analysis, sentiment, extraction, deduction. Sends results. |
| **Scheduling Agent**     | Interact with calendar/scheduling systems, suggest optimal times.       | AI-Powered Scheduling Jobs (e.g., "Analyze work calendar", "Plan my workouts") | Receives scheduling requests. Interacts with calendar APIs (Google Calendar). May use Vertex AI/optimization for suggestions. Sends suggestions/actions. |
| **Integration Agent**    | Facilitate data flow and actions between different external applications. | Workflow & Integration Jobs (e.g., "Notion task to Google Calendar event", "High-priority email notification") | Acts as a connector. Triggered by messages or events. Translates requests for external APIs. May use Vertex AI for simple data transforms. |
| **Personal Development Agent** | Provide guidance, tracking, or suggestions for personal goals/habits. | Personal Development & Coaching Jobs (e.g., "Help me build a habit", "Track emotional well-being", "Suggest a new book") | Potentially orchestrates other agents. Uses Vertex AI for personalized feedback/suggestions based on user data. Communicates via Notification Agents. |