from .base_agent import BaseAgent
from .notion_fetch_agent import NotionFetchAgent
from .scripture_generation_agent import ScriptureGenerationAgent
from .text_notification_agent import NotificationAgent

# Each agent is instantiated and registered with a unique key.
AGENT_REGISTRY = {
    "notionfetchagent": NotionFetchAgent,
    "scripturegenerationagent": ScriptureGenerationAgent,
    "notificationagent": NotificationAgent,
}

AGENT_DESCRIPTIONS = {
    "notionfetchagent": "This agent works with retrieved user Notion data (journal data for now).",
    "scripturegenerationagent": "Generates Bible scripture based on provided insights and growth goals.",
    "notificationagent": "Sends notifications to users via Twilio SMS.",
}