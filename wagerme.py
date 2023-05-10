'''
wagerme
user sends Twilio Number a wager in the form of a number (i.e. '$20')
Twilio Number replies with "what's the bet?"
user responds with memo used in lightning address
API generates lightning address
Twilio Number sends 'lnbc1...'
user pays invoice
API notifies group
group has 2 minutes to pay the invoice
bettor pays invoice
BETTING SHOWDOWN BEGINS
user gets notified that it's about to go down
when bet concludes, user replies results and bettor replies result ('I won!' or 'I lost.')
'''

'''
app flow
code->git->GitHub->heroku->twilio->phone number
phone number->twilio->heroku
'''

'''
text message wallet
if number, then generate invoice
if balance, then show balance
if invoice, decode invoice
if confirmed, then pay invoice (how can it confirm if it's a new call; need to store memory?)
need to a function to create a wallet and needs to be tied to number
need to be able to send QR codes via MMS
need to be able to read QR codes from camera via AI or other library
'''

from flask import Flask, request, redirect, render_template, jsonify
from twilio.twiml.messaging_response import MessagingResponse
import openai
from lnbits import *

import os
import subprocess
import time

openai.api_key = os.environ["openaiapikey"]
lnbitsapikey = os.environ["lnbitsapikey"]

app = Flask(__name__)
# Should be an environmental variable
app.config["SECRET_KEY"] = os.environ.get('flasksecret')

@app.route("/error", methods=['GET', 'POST'])
def error():
        # Start our TwiML response
        resp = MessagingResponse()
        reply = resp.message('try again :(')

@app.route("/sms", methods=['GET', 'POST'])
def sms_reply():
    start = time.time()
    # Get the message the user sent our Twilio number
    body = request.values.get('Body', None)
    from_number = request.values.get('From', None)
    print(body)
    print(from_number)

    """Generate a lightning invoice"""
    if body.isdigit():
        # Convert input into sats
        sats = usdtobtc(body)['sats']
        memo = 'message wallet bot'

        # Create receive address
        output = receiveinvoice(sats,memo)
        lnaddress = output[0]
        payment_hash = output[1]
        
        # Open subprocess to see if message gets paid
        subprocess.Popen(["python", "checkinvoice.py", payment_hash])

        # Start our TwiML response
        resp = MessagingResponse()
        reply = resp.message(lnaddress)

    elif body.lower() == "balance":
        # Get wallet balance (msats)
        balance = getbalance()
        balance_sats = int(balance['balance']/1000)
        wallet_name = balance['name']

        # Conversion to USD
        convert = btctousd(balance_sats)['USD']
        index = convert.index('.')
        balanceUSD = convert[:index+3]

        # Start our TwiML response
        resp = MessagingResponse()
        reply = resp.message(f'{wallet_name} has ${balanceUSD} ({balance_sats} sats)')

    elif body[0:4] == 'lnbc':
        # Decode invoice
        decode = decodeinvoice(body)
        
        # Save to local memory
        with open('address.txt', 'w') as f:
            f.write(body)

        # Start our TwiML response
        resp = MessagingResponse()
        reply = resp.message(f'Text "pay" to send ${decode[0]} for {decode[2]}')

    elif body.lower() == 'pay':
        if os.path.exists('address.txt'):
            # Read invoice from local memory
            with open('address.txt', 'r') as f:
                address = f.read()
            status = payinvoice(address)
        else:
            status = 'No payable address. Send lightning invoice.'

        if status == "Success!":
            os.remove('address.txt')

        # Start our TwiML response
        resp = MessagingResponse()
        reply = resp.message(status)

    else:
        """Send a dynamic reply to an incoming text message"""
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

        # Start our TwiML response
        resp = MessagingResponse()

        # Add a message
        reply = resp.message(msg)
        print('elasped time: ', time.time()-start)

        # # Add a picture message (.jpg, .gif)
        # reply.media(
        #     "https://media2.giphy.com/media/xT0GqjBCkO9BEiSEOk/giphy.gif"
        # )

    return str(resp)

if __name__ == "__main__":
    app.run(debug=True)