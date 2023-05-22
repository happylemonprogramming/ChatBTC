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
from PIL import Image
from urllib.parse import urlparse, parse_qs
from database import *

import os
import subprocess
import time
from io import BytesIO

openai.api_key = os.environ["openaiapikey"]
# lnbitsapikey = os.environ["lnbitsapikey"]
phone_number = os.environ['phone_number']
keys = {phone_number: lnbitsadminkey}

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get('flasksecret')

@app.route("/error", methods=['GET', 'POST'])
def error_reply():
    # Default Twilio Option: https://demo.twilio.com/welcome/sms/reply
    # Start our TwiML response
    resp = MessagingResponse()
    reply = resp.message('error, try again later :(')
    return str(resp)

@app.route("/dev", methods=['GET', 'POST'])
def development():
    img = Image.open('lightning.jpeg')
    bytes_io = BytesIO()
    img.save(bytes_io, format='BMP') # only image file type accepted without fail
    bytes_io.seek(0)  # move the cursor to the beginning of the file
    return send_file(bytes_io, mimetype='image/bmp')

@app.route("/sms", methods=['GET', 'POST'])
def sms_reply():
    start = time.time()
    # Get the message the user sent our Twilio number
    body = request.values.get('Body', None)
    from_number = request.values.get('From', None)
    num_media = int(request.values.get('NumMedia', 0))

    try:
        body = float(body)
    except:
        body = str(body)

    if body.lower() != 'accept':
        try:
            item = get_from_dynamodb(from_number)
            lnbitsadmin = item['lnbitsadmin']
            user = from_number
        except:
            user = None
    else:
        user = body

    # Confirm user
    if user == None:
        # Start our TwiML response
        resp = MessagingResponse()
        reply = resp.message('Thanks for using the bot! This bot allows users to access AI and Bitcoin, but is experimental so use at your own risk. Text "accept" to acknowledge that this service is in beta and not reponsible for any lost funds or responses provided by the AI service.')

    # User accepts terms
    elif type(body) is str and body.lower() == 'accept':
        wallet_data = createwallet(from_number)
        lnbitsadmin = wallet_data['adminkey']
        save_to_dynamodb(from_number, lnbitsadmin)
        resp = MessagingResponse()
        reply = resp.message('Your wallet has been created! AI chatbot unlocked! Text "commands" to learn more.')

    # User needs help
    elif type(body) is str and body.lower() == 'commands':
        resp = MessagingResponse()
        reply = resp.message('Text a question for the bot or use any of these commands: "balance" to view wallet balance, "$1.21" to generate invoice for $1.21, "lnbc..." to decode lightning invoice, "<MMS Image>" to decode lightning QR code')

    # Generate lightning invoice
    elif body is not None and len(str(body)) > 0 and (str(body)[0] == '$' or isinstance(body, (int, float))):
        if str(body)[0] == '$':
            body = body[1:]
        # Convert input into sats
        sats = usdtobtc(body)['sats']
        memo = 'SMS wallet bot'

        # Create receive address
        output = receiveinvoice(sats,memo,lnbitsadmin)
        lnaddress = output[0]
        payment_hash = output[1]
        
        # Create QR code
        file = create_qrcode(lnaddress, filename='lightning.jpeg')

        # Start our TwiML response
        resp = MessagingResponse()
        # Send lightning address
        reply = resp.message(lnaddress)

        # Add a picture message (.jpg, .gif)
        # Make the HEAD request
        media_url = 'https://chatbtc.herokuapp.com/dev'
        response = requests.head(media_url)

        # Print the Content-Type to verify for Twilio
        print(response.headers['Content-Type'])
        reply.media(media_url)

        # Open subprocess to see if message gets paid
        subprocess.Popen(["python", "checkinvoice.py", payment_hash, from_number, str(body)])
        # TODO: integer body reads as $100.0 instead of $100.00
        return str(resp)
    
    # Check wallet balance
    elif body.lower() == "balance" or body.lower() == "balance ": #Autocorrect adds space
        # Get wallet balance (msats)
        balance = getbalance(lnbitsadmin)
        balance_sats = int(balance['balance']/1000)
        wallet_name = balance['name']

        # Conversion to USD
        convert = str(btctousd(balance_sats)['USD'])
        index = convert.index('.')
        balanceUSD = convert[:index+3]

        # Start our TwiML response
        resp = MessagingResponse()
        reply = resp.message(f'{wallet_name} has ${balanceUSD} ({balance_sats} sats)')

    # Decode an invoice from lightning address string
    elif body[0:4] == 'lnbc':
        # Decode invoice
        decode = decodeinvoice(body, lnbitsadmin)
        
        # Save to local memory
        with open('address.txt', 'w') as f:
            f.write(body)

        # Start our TwiML response
        resp = MessagingResponse()
        if decode[2] != None:
            text = f'Text "pay" to send ${decode[0]} for {decode[2]}'
        else:
            text = f'Text "pay" to send ${decode[0]}'
        reply = resp.message(text)

    # Decode an invoice from image of QR code
    elif num_media > 0: # Assumes this is a QR code
        for i in range(num_media):
            # Get media url location
            media_url = request.values.get(f'MediaUrl{i}')
            print("User media: ", media_url)

            # Process Image
            content = process_image(media_url)
            print(content)

            # For Cashapp QR Codes
            if content.startswith("bitcoin:") or content.startswith("lightning="):
                parsed_url = urlparse(content)
                query_params = parse_qs(parsed_url.query)
                content = query_params.get('lightning', [None])[0]
            
            # Decode invoice
            decode = decodeinvoice(content, lnbitsadmin)
            print(decode)

            # Save to local memory
            with open('address.txt', 'w') as f:
                f.write(content)

            # Start our TwiML response
            resp = MessagingResponse()
            reply = resp.message(f'Text "pay" to send ${decode[0]} for {decode[2]}')

    # Pay invoice
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

    # Wrong number pay attempt error
    elif body.lower() == 'pay' and from_number != phone_number:
        # Start our TwiML response
        resp = MessagingResponse()
        reply = resp.message('Nice try :)')

    else:
        # Open subprocess to allow ChatGPT time to think
        subprocess.Popen(["python", "chatbot.py", body, from_number])
        resp = 'Thinking...' # Need these to return 'str(resp)' for higher level sms_reply() function

    return str(resp)

if __name__ == "__main__":
    app.run(debug=True)