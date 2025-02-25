from notion_client import Client
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from typing import TypedDict
import os
from langgraph.graph import END, StateGraph
from langchain.agents import initialize_agent

# Agent-dependent imports
from twilio.rest import Client as TwilioClient
from agents.notion_fetch_agent import fetch_latest_notion_journaling_entry
from agents.text_notification_agent import text_user

# Initialize clients (replace with your actual credentials)
#notion = Client(auth="your_notion_api_key")
llm = ChatOpenAI(model="gpt-4o")
#twilio_client = TwilioClient("your_account_sid", "your_auth_token")

class State(TypedDict):
    notion_data_action: str # TEMPLATE VAR
    notion_next_node_instructions: str # TEMPLATE VAR
    notion_journal_growth_summary: str # TEMPLATE VAR
    message: str # TEMPLATE VAR

# Agent 1 - Notion (TEMPLATE VARS based on whats in agent class)
notion_prompt_template = PromptTemplate(
    input_variables=["notion_data_action"],
    template="You are an assistant responsible for simply making a call to the notion client API, and then doing the following instructions on the returned data: {notion_data_action}"
)
tools = [fetch_latest_notion_journaling_entry]
notion_agent = initialize_agent(
    tools=tools,
    llm=llm,
    handle_parsing_errors=True
)
def notion_node(state: State) -> State:
    # These 2 lines wouldnt be needed in agent class code, since orchestrator injects notion_data_action into the entire code block string
    # Hence, we can just define the notion_prompt_template here as a string
    notion_data_action = state.get("notion_data_action")
    prompt = notion_prompt_template.format(notion_data_action=notion_data_action)
    result = notion_agent.invoke(prompt)
    return {"notion_journal_growth_summary": result.get('output')}

# Agent 2 - Scripture (TEMPLATE VARS based on whats in agent class)
generation_agent_instructions = """
You are a generalist assistant reponsible for performing a simple query. The 
instructions are:

{instructions}
"""
generation_agent_prompt_template = PromptTemplate(
    # TEMPLATE VAR (output of notion node or other things)
    input_variables=["instructions"],
    # TEMPLATE VAR
    template=generation_agent_instructions
)
generation_agent_llm_chain = LLMChain(llm=llm, prompt=generation_agent_prompt_template)
def generation_node(state: State) -> State:
    # Output from previous node
    # TEMPLATE VAR
    notion_journal_growth_summary = state.get("notion_journal_growth_summary")
    # TEMPLATE VAR
    notion_next_node_instructions = state.get("notion_next_node_instructions") + notion_journal_growth_summary
    
    prompt = generation_agent_prompt_template.format(instructions=notion_next_node_instructions)
    output = generation_agent_llm_chain.run(prompt)

    return {"message": output}

# Agent 3 - Twilio text (TEMPLATE VARS based on whats in agent class)
twilio_prompt_template = PromptTemplate(
    # TEMPLATE VAR (output of notion node or other things)
    input_variables=["message"],
    # TEMPLATE VAR
    template="Your sole purpose is to send this text message to the user: \"{message}\""
)
tools = [text_user]
twilio_agent = initialize_agent(
    tools=tools,
    llm=llm,
    handle_parsing_errors=True
)
def twilio_node(state: State) -> State:
    output = twilio_agent.invoke(twilio_prompt_template.format(message=state.get("message")))
    return {}

# Initialize the graph with the state schema
graph = StateGraph(State)

# Add nodes
# TEMPLATE VAR - We can loop through the nodes in the actual app
graph.add_node("notion_node", notion_node)
graph.add_node("generation_node", generation_node)
graph.add_node("twilio_node", twilio_node)

# Set the entry point
# TEMPLATE VAR
graph.set_entry_point("notion_node")

# Define sequential edges
# TEMPLATE VAR -Also loop through this
graph.add_edge("notion_node", "generation_node")
graph.add_edge("generation_node", "twilio_node")
graph.add_edge("twilio_node", END)

compiled_graph = graph.compile()


if __name__ == "__main__":
    initial_state = {
        "notion_data_action": "From this journaling, extract out the primary way the user desires to grow in his/her life.",
        "notion_next_node_instructions": "Based on this growth summary of a user's journal page, provide a single Bible scripture/verse that will help them with personal growth: "
    }
    try:
        result = compiled_graph.invoke(initial_state)
        print("Graph execution successful! Response:\n", result)
    except Exception as e:
        print(f"Graph-level error: {e}")