# agents/notification_agent.py
from agents.base_agent import BaseAgent
from typing import List
from schemas.orchestrator_schema import AgentTemplateVarInstruction

class NotificationAgent(BaseAgent):
    """
    LangGraph graph state attributes provided by this agent:
    - `message`: This can either be a simple message, or a result of other nodes 
       in the graph being called (e.g. Notion page summaries)
    """

    tool_code_import_mappings = {
       "text_user": "from tools.text_notification_agent_tools import text_user"
    }

    def __init__(self, ai_generated_template_vars: List[AgentTemplateVarInstruction],
                step: int, tools_to_use: List[str] = ["text_user"]):
        self.ai_generated_template_vars = ai_generated_template_vars
        self.step = step
        self.tools_to_use = tools_to_use

    @property
    def description(self) -> str:
        return "Sends notifications to users via Twilio SMS."
    
    def get_graph_node_code(self):
        tools_code_str = "\n".join(self.tool_code_import_mappings[x] for x in self.tools_to_use)
        tools_code_str += f"\ntools = [{', '.join(self.tools_to_use)}]"

        code = """
llm = ChatOpenAI(model="gpt-4o")
twilio_prompt_template = PromptTemplate(
    input_variables=["message"],
    template="Your sole purpose is to send this text message to the user: {message}"
)\n""" + tools_code_str + """
twilio_agent = initialize_agent(
    tools=tools,
    llm=llm,
    handle_parsing_errors=True
)
def notificationagent(state: State) -> State:
    output = twilio_agent.invoke(twilio_prompt_template.format(message=state.get("message")))
    return {}"""
        return code
    