# agents/notion_fetch_agent.py
from agents.base_agent import BaseAgent
import os
from notion_client import Client
from langchain.tools import tool
from typing import List
from schemas.orchestrator_schema import AgentTemplateVarInstruction

# Notion fetch function
# TODO: figure out auth for this, if app will go into prod eventually
@tool
def fetch_latest_notion_journaling_entry(dummy_input: str = "") -> str:
    """Fetch the latest journaling entry (page) from a Notion database (pass in a random string)."""

    # TODO: Extract this out later
    # This is my hardcoded database ID for 
    notion_db_id = "9dd35093a917436f9de6aa56b28c6182"
    notion = Client(auth=os.environ["NOTION_BEARER_TOKEN"])
    response = notion.databases.query(
        database_id=notion_db_id,
        sorts=[
            {
                "timestamp": "created_time",
                "direction": "descending"
            }
        ],
        page_size=1  # Limit to the most recent entry
    )

    def get_page_content(page_id):
        blocks = notion.blocks.children.list(block_id=page_id)
        content = []
        for block in blocks["results"]:
            block_type = block["type"]
            if block_type == "paragraph" and block["paragraph"]["rich_text"]:
                text = "".join([t["plain_text"] for t in block["paragraph"]["rich_text"]])
                content.append(f"Paragraph: {text}")
            elif block_type == "heading_1" and block["heading_1"]["rich_text"]:
                text = "".join([t["plain_text"] for t in block["heading_1"]["rich_text"]])
                content.append(f"Heading 1: {text}")
            elif block_type == "heading_2" and block["heading_2"]["rich_text"]:
                text = "".join([t["plain_text"] for t in block["heading_2"]["rich_text"]])
                content.append(f"Heading 2: {text}")
            # Add more block types as needed (e.g., "image", "to_do", etc.)
        return content

    # Process and display the results
    results = response["results"]
    output_string = ""
    for i, page in enumerate(results, 1):
        # Get the title (adjust based on your database's property name)
        title = page["properties"].get("Name", {}).get("title", [{}])[0].get("plain_text", "No title")
        created_time = page["created_time"]
        page_id = page["id"]
        
        # Fetch the page content
        content = get_page_content(page_id)
        
        # Add the page details and content to the output string
        output_string += f"{i}. Title: {title}, Created: {created_time}\n"
        if content:
            output_string += "   Content:\n"
            for line in content:
                output_string += f"      {line}\n"
        else:
            output_string += "   No content blocks found.\n"
        output_string += "\n"

    return output_string


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

    def __init__(self, ai_generated_template_vars: List[AgentTemplateVarInstruction], 
                 step: int):
        self.ai_generated_template_vars = ai_generated_template_vars
        self.step = step

    @property
    def description(self) -> str:
        return "This agent works with retrieved user Notion data (journal data for now)."

    def get_graph_node_code(self):
        code = """
tools = [fetch_latest_notion_journaling_entry]
notion_agent = initialize_agent(
    tools=tools,
    llm=llm,
    handle_parsing_errors=True
)
def notion_node(state: State) -> State:
    prompt = "You are an assistant responsible for simply making a call to the notion client API, and then doing the following instructions on the returned data: {notion_data_action}"
    result = notion_agent.invoke(prompt)
    return {"notion_journal_growth_summary": result.get('output')}
        """
        return code

    def get_post_generation_agent_code(self):
        build_prompt_py_code = """
notion_journal_growth_summary = state.get("notion_journal_growth_summary")
notion_next_node_instructions = state.get("notion_next_node_instructions") + notion_journal_growth_summary
prompt = generation_agent_prompt_template.format(instructions=notion_next_node_instructions)
        """

        return build_prompt_py_code
