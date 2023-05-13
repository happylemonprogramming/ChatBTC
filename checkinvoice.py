import time
import sys
import os

from twilio.rest import Client
from lnbits import checkstatus

# Start clock and retreive argument
start = time.time()
payment_hash = sys.argv[1]
from_number = sys.argv[2]
amount = sys.argv[3]

# payment_hash = 'eb1256a1fc76209ba188c11892c6ec5bd83c03700ab1e7518f59fb192a6e78d6'
# from_number = '+19092137231'

# Environment variables
twilioaccountsid = os.environ["twilioaccountsid"]
twilioauthtoken = os.environ["twilioauthtoken"]

# Invoice check loop
while True:
    output = checkstatus(payment_hash)
    # output = {'paid': False, 'preimage': '000...', 
    #           'details': {'checking_id': 'eb1256...', 'pending': True, 
    #           'amount': 2000, 'fee': 0, 'memo': 'yo', 'time': 1683954630, 
    #           'bolt11': 'lnbc...', 'preimage': '000...', 'payment_hash': 'eb1256...', 
    #           'expiry': 1683955230.0, 'extra': {}, 'wallet_id': '86...', 'webhook': None, 
    #           'webhook_status': None}}

    if time.time() - start > 120:
        msg = 'Invoice Expired'
        break
    elif output['paid'] == True:
        msg = f'Received ${amount}'
        break
    else:
        elasped_time = time.time()-start
        print(output['paid'], elasped_time)
        time.sleep(2)

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
print("Text Message ID: ", message.sid)