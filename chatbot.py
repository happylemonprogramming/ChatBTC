"""Send a dynamic reply to an incoming text message"""
import openai
import os
import sys
from twilio.rest import Client

# Environment variables
twilioaccountsid = os.environ["twilioaccountsid"]
twilioauthtoken = os.environ["twilioauthtoken"]
openai.api_key = os.environ["openaiapikey"]

body = sys.argv[1]
from_number = sys.argv[2]

# AI integration
output = openai.ChatCompletion.create(
model="gpt-3.5-turbo",
messages=[
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": body}
    # TODO consider recursive calls to the assistant that allows the assistant to have context
    ]
)

cost = float(0.002 * int(output['usage']['total_tokens'])/1000)
print(f"Cost: ${cost}")
msg = output['choices'][0]['message']['content']

# Twilio account verification
account_sid = twilioaccountsid
auth_token = twilioauthtoken
client = Client(account_sid, auth_token)

# Text message
message = client.messages.create(
from_='+19098940201',
to=from_number,
body=msg
)

# Heroku prints
print(message.sid)
print('Text Message Sent')