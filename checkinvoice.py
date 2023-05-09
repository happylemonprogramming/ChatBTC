import time
import sys
import os

from twilio.rest import Client
from lnbits import checkstatus

# Start clock and retreive argument
start = time.time()
payment_hash = sys.argv[1]

# Environment variables
twilioaccountsid = os.environ["twilioaccountsid"]
twilioauthtoken = os.environ["twilioauthtoken"]

# Invoice check loop
while True:
    output = checkstatus(payment_hash)
    if time.time() - start > 120:
        msg = output
        break
    elif output['paid'] is True: #need to confirm output
        msg = 'PAID'
        break
    else:
        elasped_time = time.time()-start
        print(elasped_time)
        time.sleep(2)

# Twilio account verification
account_sid = twilioaccountsid
auth_token = twilioauthtoken
client = Client(account_sid, auth_token)

# Text message
message = client.messages.create(
from_='+19098940201',
to='+19092137231',
body=msg
)

# Heroku prints
print(message.sid)
print('Text Message Sent')