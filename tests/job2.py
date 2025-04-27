# This is a more realistic, sample langgraph flow/job that would run in Google Cloud Run

from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from typing import TypedDict
import os
from langgraph.graph import START, END, StateGraph
from langchain.agents import initialize_agent

class State(TypedDict):
    notion_journal_growth_summary: str
    notion_next_node_instructions: str
    message: str

graph = StateGraph(State)


llm = ChatOpenAI(model="gpt-4o")
from tools.notion_fetch_agent_tools import fetch_latest_notion_journaling_entry
tools = [fetch_latest_notion_journaling_entry]
notion_agent = initialize_agent(
    tools=tools,
    llm=llm,
    handle_parsing_errors=True
)
def notionfetchagent(state: State) -> State:
    prompt = "You are an assistant responsible for simply making a call to the notion client API, and then doing the following instructions on the returned data: Analyze the content from the user's Notion journal entry and extract the most relevant keywords that reflect core themes or focus areas. Return a list of keywords that encapsulate the primary subjects and intentions stated by the user."
    result = notion_agent.invoke(prompt)
    return {"notion_journal_growth_summary": result.get('output')}


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

    
    notion_journal_growth_summary = state.get("notion_journal_growth_summary")
    notion_next_node_instructions = state.get("notion_next_node_instructions") + notion_journal_growth_summary
    prompt = generation_agent_prompt_template.format(instructions=notion_next_node_instructions)
            
    output = generation_agent_llm_chain.run(prompt)

    return {"message": output}
        


llm = ChatOpenAI(model="gpt-4o")
twilio_prompt_template = PromptTemplate(
    input_variables=["message"],
    template="Your sole purpose is to send this text message to the user: {message}"
)
from tools.text_notification_agent_tools import text_user
tools = [text_user]
twilio_agent = initialize_agent(
    tools=tools,
    llm=llm,
    handle_parsing_errors=True
)
def notificationagent(state: State) -> State:
    output = twilio_agent.invoke(twilio_prompt_template.format(message=state.get("message")))
    return {}

graph.add_node("notionfetchagent", notionfetchagent)

graph.add_node("generationagent", generationagent)

graph.add_node("notificationagent", notificationagent)

graph.add_edge(START, "notionfetchagent")

graph.add_edge("notionfetchagent", "generationagent")

graph.add_edge("generationagent", "notificationagent")

graph.add_edge("notificationagent", END)


compiled_graph = graph.compile()

if __name__ == "__main__":
    # TODO: implement some logic in build_and_render_ai_job_workflow() that adds to initial state,
    # the template vars that were not already injected in node code
    initial_state = {
        "notion_next_node_instructions": "Based on this growth summary of a user's journal page, provide a single Bible scripture/verse that will help them with personal growth: "
    }
    try:
        result = compiled_graph.invoke(initial_state)
        print("Graph execution successful! Response: ", result)
    except Exception as e:
        print(f"Graph-level error: {e}") 