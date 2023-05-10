import time
import sys
import os

from twilio.rest import Client
from lnbits import payinvoice

# Start clock and retreive argument
start = time.time()
from_number = sys.argv[1]

# Environment variables
twilioaccountsid = os.environ["twilioaccountsid"]
twilioauthtoken = os.environ["twilioauthtoken"]

# Read invoice from local memory
with open('address.txt', 'r') as f:
    address = f.read()
status = payinvoice(address)

# Remove temp file
if status == "Success!":
    os.remove('address.txt')

# Twilio account verification
account_sid = twilioaccountsid
auth_token = twilioauthtoken
client = Client(account_sid, auth_token)

# Text message
message = client.messages.create(
from_='+19098940201',
to=from_number,
body=status
)

# Heroku prints
print(message.sid)
print('Text Message Sent')