'''This function checks that status of the latest invoice created and notifies the user of the status'''

import time
import sys
from twilioapi import *
from lnbits import checkstatus

# Start clock and retreive argument
start = time.time()
payment_hash = sys.argv[1]
number = sys.argv[2]
amount = sys.argv[3]
lnbitsadmin = sys.argv[4]

# Convert amount to dollar unit format $X.XX
amount = "{:.2f}".format(float(amount))

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
    print(output)
    current_time = output['details']['time']
    expiry = output['details']['expiry']
    print(current_time, expiry,expiry-current_time)
    if current_time>expiry:
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

# Send text notification
smstext(number, msg, media_url=None)