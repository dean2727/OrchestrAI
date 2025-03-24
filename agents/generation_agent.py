# agents/scripture_generation_agent.py
from agents.base_agent import BaseAgent
from typing import List
from schemas.orchestrator_schema import AgentTemplateVarInstruction

class GenerationAgent(BaseAgent):

    template_var_instructions = {
        "instructions": """This should be instructions to the first agent, which does a basic generation query.
Some examples:
1. Generate the ideas on how to improve productivity
2. Generate the motivational quote
3. Summarize the concept""",
        "build_prompt_py_code": "Just give back a random word."
    }

    state_vars_set = {"generation_message": str}

    # for now, this isnt needed, since we're just assuming instructions are applied 
    # if and only if this type of agent is first in the AI job chain
    instructions_provided = False

    def __init__(self, ai_generated_template_vars: List[AgentTemplateVarInstruction], 
                step: int):
        self.ai_generated_template_vars = ai_generated_template_vars
        self.step = step

    @property
    def description(self) -> str:
        return "Vanilla generation agent ."

    def get_graph_node_code(self):
        code = """
# Initialize the ChatOpenAI model
llm = ChatOpenAI(model="gpt-4o")

# Create a prompt template
generation_agent_prompt = PromptTemplate(
    input_variables=["instructions"],
    template="You are a generalist assistant reponsible for performing a simple query. The instructions are: {instructions}"
)

# Create the chain using the runnables API (prompt | llm | parser)
generation_agent_chain = generation_agent_prompt | llm | StrOutputParser()

def generationagent(state: State) -> State:
    # Get necessary context from state
    {build_prompt_py_code}
    
    # Invoke generation with the chain
    response = generation_agent_chain.invoke({"instructions": prompt})

    return {"generation_message": response}
        """
        return code