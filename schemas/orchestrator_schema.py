from typing import List, Optional, Dict
from pydantic import BaseModel

class OrchestratorOutputFormat(BaseModel):
    message: str
    agents: Optional[List[str]]

class AgentTemplateVarInstruction(BaseModel):
    template_var_name: str
    template_var_instruction: str

class AgentTemplateVarInstructionsOutputFormat(BaseModel):
    ai_generated_template_vars: List[AgentTemplateVarInstruction]