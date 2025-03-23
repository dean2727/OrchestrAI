# agents/notion_fetch_agent.py
from agents.base_agent import BaseAgent
import os
from typing import List
from schemas.orchestrator_schema import AgentTemplateVarInstruction

class NotionFetchAgent(BaseAgent):
    """
    LangGraph graph state attributes provided by this agent (* indicates provided by orchestrator to the jinja template):
    - *`notion_data_action` (str; State attribute): Specifies what the LLM should 
       do on the returned Notion data.
    - `notion_journal_growth_summary` (str; State attribute): Holds a summary 
       of the user's desires for personal growth (from the journal page) (post-node output).
    - *`notion_next_node_instructions` (str; State attribute): Tells the next node 
       that comes after it what to do with the `notion_journal_growth_summary`.

    This agent operates under the following assumptions/constraints:
    - It has access to a tool which pulls from a given user's DB, and accesses 
      the most recent row/page (journal entry for testing purposes)
    """

    template_var_instructions = {
        "notion_data_action": """
This should be an action that will be taken on the user's Notion data. A 
general template is something like "Analyze the content from the user's 
Notion page and <desired_analysis>. Return a <output_format> that captures 
<goal>.". Some other examples:

1.	Summarization Task:
"Analyze the content from the user's Notion journal entry and summarize the primary ways the user desires personal growth. Return a concise paragraph that highlights their key motivations and intentions."
2.	Sentiment Analysis Task:
"Analyze the emotional tone of the user's journal entry and return a summary of the prevailing emotions expressed by the user."
3.	Keyword Extraction Task:
"Extract the most relevant keywords from the user's Notion journal entry that reflect core themes or focus areas."
4.	Action Item Identification:
"Analyze the user's journal entry and identify specific action items or goals the user mentioned."
        """,

        "notion_next_node_instructions": """
This should explain what to do with the output from the Notion data processing.
A general template is something like "Based on the <data_summary> from the 
user's journal entry, <desired_output_action> to <help_with_purpose>.". 
Some other examples:

1.	Scripture Generation Task:
"Based on the summarized growth goals from the user's journal, provide a single Bible scripture that encourages and supports the user's desired personal growth."
2.	Motivational Quote Retrieval:
"Using the extracted insights from the user's journal, find a motivational quote that aligns with the user's expressed goals or emotions."
3.	Task Suggestion:
"Based on the journal's extracted action items, suggest one small, practical step the user can take to move forward."
4.	Daily Reflection Prompt:
"Using the main themes from the journal summary, generate a reflective question the user can think about for personal growth."
        """
    }

    state_vars_set = {"notion_journal_growth_summary": str}

    tool_code_import_mappings = {
        "fetch_latest_notion_journaling_entry": "from tools.notion_fetch_agent_tools import fetch_latest_notion_journaling_entry"
    }

    def __init__(self, ai_generated_template_vars: List[AgentTemplateVarInstruction], 
                 step: int, tools_to_use: List[str] = ["fetch_latest_notion_journaling_entry"]):
        self.ai_generated_template_vars = ai_generated_template_vars
        self.step = step
        self.tools_to_use = tools_to_use

    @property
    def description(self) -> str:
        return "This agent works with retrieved user Notion data (journal data for now)."

    # TODO: need to implement a mechanism for the orchestrator to only get template vars
    # for a determined agent, but also the tools it will have access to
    # tools can all be mounted in the cronjob and imported into this code as needed
    def get_graph_node_code(self):
        tools_code_str = "\n".join(self.tool_code_import_mappings[x] for x in self.tools_to_use)
        tools_code_str += f"\ntools = [{', '.join(self.tools_to_use)}]"

        code = "llm = ChatOpenAI(model=\"gpt-4o\")" + "\n" + tools_code_str + """
notion_agent = initialize_agent(
    tools=tools,
    llm=llm,
    handle_parsing_errors=True
)
def notionfetchagent(state: State) -> State:
    prompt = "You are an assistant responsible for simply making a call to the notion client API, and then doing the following instructions on the returned data: {notion_data_action}"
    result = notion_agent.invoke(prompt)
    return {"notion_journal_growth_summary": result.get('output')}"""
        return code

    # TODO: this also depends on what tools are used/what function this agent would 
    # serve in the job. This needs to be dynamically determined somehow (perhaps 
    # with if-else is easiest)
    def get_proceeding_agent_code(self):
        if "fetch_latest_notion_journaling_entry" in self.tools_to_use:
            build_prompt_py_code = """
    notion_journal_growth_summary = state.get("notion_journal_growth_summary")
    notion_next_node_instructions = state.get("notion_next_node_instructions") + notion_journal_growth_summary
    prompt = generation_agent_prompt_template.format(instructions=notion_next_node_instructions)
            """
        else:
            build_prompt_py_code = "..."

        return build_prompt_py_code
