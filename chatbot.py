"""Send a dynamic reply via Artificial Intelligence to any incoming text message"""

import openai
import os
import sys
from twilioapi import *

# Environment variables
openai.api_key = os.environ["openaiapikey"]

body = sys.argv[1]
from_number = sys.argv[2]

try:
    # AI integration
    output = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
            # TODO consider allowing user to create their own prompt as a function
            # The prompt can be anything: a therapist, doctor, mechanic, friend, teacher, etc...
        {"role": "user", "content": body}
            # TODO consider recursive calls to the assistant that allows the assistant to have context
        ]
    )
    print(output['choices'][0]['message']['content'])
except:
    smstext(from_number, 'Try again later, AI server overloaded :(', media_url=None)

# Total AI cost, does not include Twilio fees or Carrier SMS/MMS fees
cost = float(0.002 * int(output['usage']['total_tokens'])/1000)
print(f"Cost: ${cost}")

msg = output['choices'][0]['message']['content']
msglength = len(str(msg))

chunks = []

# Necessarily splits texts in case the response is too long to be combined by service provider
if msglength > 1500:
    # Split the message into chunks of 1600 characters
    chunks = [msg[i:i+1500] for i in range(0, msglength, 1500)] #character buffer for /n
else:
    chunks.append(msg)

for content in chunks:
    msg = content
    smstext(from_number, msg, media_url=None)