from openai import OpenAI
import os
from pydantic import RootModel, BaseModel
from agents import AGENT_REGISTRY
from typing import Union, List, Optional
from orchestrator.orchestrator import Orchestrator

orchestrator = Orchestrator()

query = "Send me bible scripture that will help me with how i want to grow from my latest journaling in Notion."

# Test agent determination
ai_response = orchestrator.determine_agents(query)
agents = ai_response.agents
print(ai_response)

# Determine template vars
agents = orchestrator.initialize_agents(query, agents)
# for agent in agents:
#     print(agent)

# Render the workflow (python file)
template_save_path = "test.py"
orchestrator.build_and_render_ai_job_workflow(agents, output_file_path=template_save_path)