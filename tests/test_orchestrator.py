import chainlit as cl
from kubernetes_cronjob_manager import create_cronjob
from openai import OpenAI
import os
from pydantic import RootModel, BaseModel
from agents import AGENT_REGISTRY
from typing import Union, List, Optional

# 2 models needed, since response_format isnt supported with o1 model
reasoning_model = "o1-mini-2024-09-12"
non_reasoning_model = "gpt-4o"

agent_descriptions = "\n".join(
    [f"{name}: {agent.description}" for name, agent in AGENT_REGISTRY.items()]
)


class OrchestratorOutputFormat(BaseModel):
    message: str
    agents: Optional[List[str]]

test = "Send me bible scripture that will help me with how i want to grow from my latest journaling in Notion."

orchestrator_instructions_get_job_agents = """
You are a helpful assistant working in an application that will help the user 
automate recurring tasks in their life, by setting up a cronjob for them, which 
will execute a sequence of AI agents that each have different purposes. You have 
access to the following agent pool:

{agent_descriptions}

Your job is to first think through what steps/stages need to go into properly 
fulfilling this request. Then, map these steps to the agents in the agent pool,
and determine if the pool can provide you with all the necessary agents. If you 
find that the pool does include all necessary agents, return back the list of 
agents in the order they should be executed in the cronjob. Otherwise, if the 
pool does not have all necessary agents, then return a string message saying so.

User query:
{query}
""".format(agent_descriptions=agent_descriptions, query=test)

orchestrator_instructions_format_job_agents = """
Your goal is to simply parse out the agent names into a list in the order that 
you see them, from this message:

{message}

If you see no ordered list and instead some message that the agent pool does 
not have all necessary agents, just return back this same message.
"""

orchestrator = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),  # This is the default and can be omitted
)

chat_completion = orchestrator.beta.chat.completions.parse(
    model=reasoning_model,
    messages=[
        {
            "role": "user",
            "content": orchestrator_instructions_get_job_agents,
        }
    ],
)

chat_completion = chat_completion.choices[0].message.content

# Print the response
print(chat_completion)

chat_completion = orchestrator.beta.chat.completions.parse(
    model=non_reasoning_model,
    messages=[
        {
            "role": "user",
            "content": orchestrator_instructions_format_job_agents.format(message=chat_completion),
        }
    ],
    response_format=OrchestratorOutputFormat
)

agents = chat_completion.choices[0].message.parsed.agents
print(agents)
