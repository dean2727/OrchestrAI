from twilio.rest import Client
from langchain.tools import tool

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