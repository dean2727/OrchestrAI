# agents/notification_agent.py
from agents.base_agent import BaseAgent
from twilio.rest import Client
from langchain.tools import tool
from typing import List
from schemas.orchestrator_schema import AgentTemplateVarInstruction

@tool
def text_user(from_num: str, to_num: str, msg: str) -> str:
    """Tool to text the user via Twilio."""
    # account_sid = os.getenv("TWILIO_ACCOUNT_SID") # TODO: get these
    # auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    # from_number = os.getenv("TWILIO_FROM_NUMBER")
    # client = Client(account_sid, auth_token)
    # sms = client.messages.create(
    #     body=msg,
    #     from_=from_num,
    #     to=to_num
    # )
    #return sms.sid
    print(msg, "sent!")
    return msg

class NotificationAgent(BaseAgent):
    """
    LangGraph graph state attributes provided by this agent:
    - `message`: This can either be a simple message, or a result of other nodes 
       in the graph being called (e.g. Notion page summaries)
    """
    def __init__(self, ai_generated_template_vars: List[AgentTemplateVarInstruction],
                step: int):
        self.ai_generated_template_vars = ai_generated_template_vars
        self.step = step

    @property
    def description(self) -> str:
        return "Sends notifications to users via Twilio SMS."
    
    def get_graph_node_code(self):
        code = """
llm = ChatOpenAI(model="gpt-4o")
twilio_prompt_template = PromptTemplate(
    input_variables=["message"],
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
        """
        return code
    