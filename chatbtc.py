'''
app flow
code->git->GitHub->heroku->twilio->phone number
phone number->twilio->heroku
'''

'''
ChatBTC

chatbot
give AI to all SMS users
TODO: allow user to set their own prompt for bot

wallet
give wallet to all SMS users
TODO: need to a function to create a wallet and needs to be tied to number
TODO: need to be able to read QR codes from camera via AI or other library
TODO: have wallets bound to phone numbers so that you can send bitcoin via phone number
TODO: need a more consistent method of payment (cashapp and wallet of satoshi fail; strike ok)
'''

from flask import Flask, request, send_file, redirect, render_template, jsonify
from twilio.twiml.messaging_response import MessagingResponse
import openai
from lnbits import *
from qrsms import *
from cloud import *

import os
import subprocess
import time
from io import BytesIO

openai.api_key = os.environ["openaiapikey"]
lnbitsapikey = os.environ["lnbitsapikey"]
phone_number = os.environ['phone_number']

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get('flasksecret')

@app.route("/error", methods=['GET', 'POST'])
def error_reply():
    # Default Twilio Option: https://demo.twilio.com/welcome/sms/reply
    # Start our TwiML response
    resp = MessagingResponse()
    reply = resp.message('error, try again later :(')
    return str(resp)

@app.route("/sms", methods=['GET', 'POST'])
def sms_reply():
    start = time.time()
    # Get the message the user sent our Twilio number
    body = request.values.get('Body', None)
    from_number = request.values.get('From', None)
    num_media = int(request.values.get('NumMedia', 0))
    
    print(from_number)
    print(body, type(body))

    try:
        body = float(body)
    except:
        body = str(body)

    """Generate a lightning invoice"""
    if str(body)[0] == '$' or isinstance(body, (int, float)):
        if str(body)[0] == '$':
            body = body[1:]
        # Convert input into sats
        sats = usdtobtc(body)['sats']
        memo = 'message wallet bot'

        # Create receive address
        output = receiveinvoice(sats,memo)
        lnaddress = output[0]
        payment_hash = output[1]
        
        # TODO: Creates QR code and uploads to AWS to get url to pass as reply.media(link)
        # Create QR code
        file = create_qrcode(lnaddress, filename='qrcode.jpeg')
        img_io = BytesIO()
        file[1].save(img_io, 'jpeg')
        img_io.seek(0)

        # # Save to server
        # link = serverlink(file)
        # print("S3 url: ", link)

        # Start our TwiML response
        resp = MessagingResponse()
        # Send lightning address
        reply = resp.message(lnaddress)
        # TODO: Twilio gives MIME-CONTENT error for link
        # Add a picture message (.jpg, .gif)
        reply.media(f'https://chatbtc.herokuapp.com/{file[0]}')

        # Open subprocess to see if message gets paid
        subprocess.Popen(["python", "checkinvoice.py", payment_hash, from_number, str(body)])
        # TODO: integer body reads as $100.0 instead of $100.00
        return send_file(img_io, mimetype='image/jpeg'), str(resp)
    
    elif body.lower() == "balance":
        # Get wallet balance (msats)
        balance = getbalance()
        balance_sats = int(balance['balance']/1000)
        wallet_name = balance['name']

        # Conversion to USD
        convert = str(btctousd(balance_sats)['USD'])
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

    elif body.lower() == 'pay' and from_number == phone_number:
        if os.path.exists('address.txt'):
            # Open subprocess to pay
            subprocess.Popen(["python", "payinvoice.py", from_number])
            status = 'In process...'
        else:
            status = 'No payable address. Send lightning invoice.'

        # Start our TwiML response
        resp = MessagingResponse()
        reply = resp.message(status)

    elif body.lower() == 'pay' and from_number != phone_number:
        # Start our TwiML response
        resp = MessagingResponse()
        reply = resp.message('Nice try :)')

    # TODO: untested; decodes QR code image sent by user into lightning invoice, saves as txt, then notifies user
    # elif num_media > 0: # Assumes this is a QR code
    #     for i in range(num_media):
    #         # Decode QR code image into text (lnbc)
    #         media_url = request.values.get(f'MediaUrl{i}')
    #         print("User media: ", media_url)

    #         # Save address from QR code string
    #         lnaddress = read_qrcode(media_url)
    #         # Decode invoice
    #         decode = decodeinvoice(body)

    #         # Save to local memory
    #         with open('address.txt', 'w') as f:
    #             f.write(body)

    #         # Start our TwiML response
    #         resp = MessagingResponse()
    #         reply = resp.message(f'Text "pay" to send ${decode[0]} for {decode[2]}')

    else:
        # Open subprocess to allow ChatGPT time to think
        subprocess.Popen(["python", "chatbot.py", body, from_number])
        resp = 'Thinking...'

    return str(resp)

if __name__ == "__main__":
    app.run(debug=True)