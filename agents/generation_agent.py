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
        return "Vanilla generation agent ."

    def get_graph_node_code(self):
        code = """
llm = ChatOpenAI(model="gpt-4o")
generation_agent_prompt_template = PromptTemplate(
    input_variables=["instructions"],
    template="You are a generalist assistant reponsible for performing a simple query. The instructions are: {instructions}"
)
generation_agent_llm_chain = LLMChain(llm=llm, prompt=generation_agent_prompt_template)
def generationagent(state: State) -> State:
    # e.g. for build_prompt_py_code:
    # notion_journal_growth_summary = state.get("notion_journal_growth_summary")
    # notion_next_node_instructions = state.get("notion_next_node_instructions") + notion_journal_growth_summary
    # prompt = generation_agent_prompt_template.format(instructions=notion_next_node_instructions)
    {build_prompt_py_code}
    output = generation_agent_llm_chain.run(prompt)

    return {"message": output}
        """
        return code