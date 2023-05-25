'''This function checks that status of the latest invoice created and notifies the user of the status'''

import time
import sys
import os

# from twilio.rest import Client
from twilioapi import *
from lnbits import checkstatus

# Start clock and retreive argument
start = time.time()
payment_hash = sys.argv[1]
number = sys.argv[2]
amount = sys.argv[3]
lnbitsadmin = sys.argv[4]

# Environment variables
twilioaccountsid = os.environ["twilioaccountsid"]
twilioauthtoken = os.environ["twilioauthtoken"]

# Invoice check loop
while True:
    output = checkstatus(payment_hash, lnbitsadmin)
    ''' Example:
         output = {'paid': False, 'preimage': '000...', 
               'details': {'checking_id': 'eb1256...', 'pending': True, 
               'amount': 2000, 'fee': 0, 'memo': 'yo', 'time': 1683954630, 
               'bolt11': 'lnbc...', 'preimage': '000...', 'payment_hash': 'eb1256...', 
               'expiry': 1683955230.0, 'extra': {}, 'wallet_id': '86...', 'webhook': None, 
               'webhook_status': None}}
    '''
    if output['time']>output['expiry']:
    # if time.time() - start > 600: #10-minute expiration time
        msg = f'${amount} Invoice Expired'
        break
    elif output['paid'] == True:
        msg = f'Received ${amount}'
        break
    else:
        elasped_time = time.time()-start
        print(f"Invoice Paid: {output['paid']}. Elasped Time: {elasped_time}")
        time.sleep(2)


smstext(number, msg, media_url=None)

# # Twilio account verification
# account_sid = twilioaccountsid
# auth_token = twilioauthtoken
# client = Client(account_sid, auth_token)

# # Text message
# message = client.messages.create(
# from_='+19098940201',
# to=number,
# body=msg
# )

# # Heroku prints
# print("Text Message ID: ", message.sid)