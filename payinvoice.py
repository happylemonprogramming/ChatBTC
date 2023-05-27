'''Reads invoice from local file on server storage and pays via lnbits API then notifies user'''

import time
import sys
from lnbits import payinvoice
from twilioapi import *

# Start clock and retreive argument
start = time.time()
lninvoice = sys.argv[1]
lnbitsadmin = sys.argv[2]
number = sys.argv[3]

# Pay invoice and save response
status = payinvoice(lninvoice, lnbitsadmin)
print(status)
# Send text notification
smstext(number, status, media_url=None)