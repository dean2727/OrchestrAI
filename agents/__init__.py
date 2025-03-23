from .base_agent import BaseAgent
from .notion_fetch_agent import NotionFetchAgent
from .generation_agent import GenerationAgent
from .text_notification_agent import NotificationAgent
from .reasoning_agent import ReasoningAgent

# Each agent is instantiated and registered with a unique key.
AGENT_REGISTRY = {
    "notionfetchagent": NotionFetchAgent,
    "generationagent": GenerationAgent,
    "notificationagent": NotificationAgent,
    "reasoningagent": ReasoningAgent
}

AGENT_DESCRIPTIONS = {
    "notionfetchagent": "This agent works with retrieved user Notion data (journal data for now).",
    "generationagent": """This agent is a vanilla generation agent which transforms text. Think of it 
as your default agent which will do basic things like summarize, answer basic questions, or generate 
creative content. However, it has its limitations: Limited reasoning, potential for hallucinations or inconsistent logic.
""",
    "reasoningagent": """This agent is like generationagent, but with a much better ability to handle the 
more complex tasks, involving logical problem-solving, analytical tasks, or structured reasoning. It is the 
chosen choice for tasks like solving math problems, making analytical judgements over some research, deducing 
a sequence of actions from some assumptions or known information, and performing step-by-step reasoning on how to 
tackle a non-obvious problem.""",
    "notificationagent": "Sends notifications to users via Twilio SMS.",
}