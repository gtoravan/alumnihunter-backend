# graditude/twilio_handler.py

from twilio.rest import Client
import os

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
PUBLIC_URL = os.getenv("PUBLIC_URL")

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

def start_call(phone_number: str):
    """
    Starts a voice call to the given phone number, routing to Vocode's webhook.
    """
    call = client.calls.create(
        to=phone_number,
        from_=TWILIO_PHONE_NUMBER,
        url=f"{PUBLIC_URL}/twilio/inbound",  # This must hit your Vocode call handler
        method="POST"
    )
    return call.sid
