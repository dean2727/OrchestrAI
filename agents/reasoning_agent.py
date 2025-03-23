from agents.base_agent import BaseAgent
from typing import List
from schemas.orchestrator_schema import AgentTemplateVarInstruction

class ReasoningAgent(BaseAgent):

    template_var_instructions = {
        "instructions": """This should be instructions to the reasoning agent, which uses DeepSeek for advanced reasoning.
Some examples:
1. Analyze the text and provide key insights with reasoning
2. Explain the concept with step-by-step reasoning
3. Compare these ideas and explain your reasoning""",
        "build_prompt_py_code": "notion_journal_growth_summary = state.get(\"notion_journal_growth_summary\")\nnotion_next_node_instructions = state.get(\"notion_next_node_instructions\") + notion_journal_growth_summary\nprompt = notion_next_node_instructions"
    }

    state_vars_set = {"message": str}

    # for now, this isnt needed, since we're just assuming instructions are applied 
    # if and only if this type of agent is first in the AI job chain
    instructions_provided = False

    def __init__(self, ai_generated_template_vars: List[AgentTemplateVarInstruction], 
                step: int):
        self.ai_generated_template_vars = ai_generated_template_vars
        self.step = step

    @property
    def description(self) -> str:
        return "Generates content with step-by-step reasoning using DeepSeek's advanced reasoning capabilities."

    def get_graph_node_code(self):
        code = """
from langchain_deepseek import ChatDeepSeek
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Initialize the ChatDeepSeek model
llm = ChatDeepSeek(
    model="deepseek-reasoner",
    temperature=0.7,
    max_tokens=None,
    timeout=None,
    max_retries=2,
)

# Create a prompt template
reasoning_prompt = PromptTemplate(
    input_variables=["instructions"],
    template=\"\"\"
You are an agent with reasoning capabilities, responsible for the following:

{instructions}
\"\"\"
)

# Create the chain using the runnables API (prompt | llm | parser)
reasoning_chain = reasoning_prompt | llm | StrOutputParser()

def reasoninggenerationagent(state: State) -> State:
    # Get necessary context from state
    {build_prompt_py_code}
    
    # Invoke reasoning with DeepSeek
    response = reasoning_chain.invoke({"instructions": prompt})

    return {"message": response}
        """
        return code
