'''Reads invoice from local file on server storage and pays via lnbits API then notifies user'''

import time
import sys
# import os

# from twilio.rest import Client
from lnbits import payinvoice
from twilioapi import *
# from database import get_from_dynamodb

# Start clock and retreive argument
start = time.time()
lninvoice = sys.argv[1]
lnbitsadmin = sys.argv[2]
number = sys.argv[3]



# item = get_from_dynamodb(from_number)
# lninvoice = item['lninvoice']
status = payinvoice(lninvoice, lnbitsadmin)

smstext(number, status, media_url=None)

# # Environment variables
# twilioaccountsid = os.environ["twilioaccountsid"]
# twilioauthtoken = os.environ["twilioauthtoken"]

# # Twilio account verification
# account_sid = twilioaccountsid
# auth_token = twilioauthtoken
# client = Client(account_sid, auth_token)

# # Text message
# message = client.messages.create(
# from_='+19098940201',
# to=number,
# body=status
# )

# # Heroku prints
# print("Text Message ID: ", message.sid)