# agents/scripture_generation_agent.py
from agents.base_agent import BaseAgent
from typing import List, Dict

class ScriptureGenerationAgent(BaseAgent):
    """
    """

    template_var_instructions = {
        "instructions": """
        This should be instructions to the first agent, which does a basic generation query.
        Some examples:
        1. Generate the ideas on how to improve productivity
        2. Generate the motivational quote
        3. Summarize the concept
        """,
    }

    instructions_provided = False

    def __init__(self, ai_generated_template_vars: Dict[str, str], step: int, precedes_generation_agent: bool):
        self.ai_generated_template_vars = ai_generated_template_vars
        self.step = step
        self.precedes_generation_agent = precedes_generation_agent # Since this is true, we define a method to get (in generation agent)

    @property
    def description(self) -> str:
        return "Generates Bible scripture based on provided insights and growth goals."

    def get_graph_node_code(self):
        code = """
        generation_agent_prompt_template = PromptTemplate(
            input_variables=["instructions"],
            template="You are a generalist assistant reponsible for performing a simple query. The instructions are: {instructions}"
        )
        generation_agent_llm_chain = LLMChain(llm=llm, prompt=generation_agent_prompt_template)
        def generation_node(state: State) -> State:
            # e.g. for build_prompt_py_code:
            # notion_journal_growth_summary = state.get("notion_journal_growth_summary")
            # notion_next_node_instructions = state.get("notion_next_node_instructions") + notion_journal_growth_summary
            # prompt = generation_agent_prompt_template.format(instructions=notion_next_node_instructions)
            {build_prompt_py_code}
            output = generation_agent_llm_chain.run(prompt)

            return {"message": output}
        """
        return code