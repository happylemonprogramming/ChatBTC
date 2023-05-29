'''
app flow
code->git->GitHub->heroku->twilio->phone number
phone number->twilio->heroku
'''

'''
ChatBTC

chatbot
give AI to all SMS users
TODO: allow user to set their own prompt for bot; can be achieved via AWS Database per user
TODO: add api with weather (important for farmers); think of ways to incorporate AI to interface with the weather based on text
    -"what's the weather like today in  

wallet
give banking to all SMS users
TODO: add whatsapp
TODO: add LNURL
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
from extractnumber import *
from twilioapi import *
from weather import *

import os
import subprocess
import time
from io import BytesIO
import uuid

openai.api_key = os.environ["openaiapikey"]
# phone_number = os.environ['phone_number']

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
    # # Generate a unique identifier and convert it to a string
    # unique_id = str(uuid.uuid4())
    # # Use the unique identifier in a filename
    # filename = f"lninvoice_{unique_id}.jpeg"
    # get_from_dynamodb(phone_number)
    # TODO: can't do unique ID because it needs to pass from server, but can't access server because number isn't passed
    img = Image.open("lightning.jpeg")
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

    # Confirm user is in database
    try:
        item = get_from_dynamodb(from_number)
        lnbitsadmin = item['lnbitsadmin']
        # TODO: store password for future payments
        user = from_number
    except:
        user = None

    # Service agreement
    if user == None and (body.lower() != 'accept' or body.lower() != "accept "):
        # Start our TwiML response
        resp = MessagingResponse()
        reply = resp.message('Thanks for using the bot! This bot allows users to access AI and Bitcoin, but is experimental so use at your own risk. Text "accept" to acknowledge that this service is in beta and not reponsible for any lost funds or responses provided by the AI service.')

    # User accepts terms
    elif type(body) is str and (body.lower() == 'accept' or body.lower() == "accept ") and user == None:
        wallet_data = createwallet(from_number)
        lnbitsadmin = wallet_data['adminkey']
        save_to_dynamodb(from_number, lnbitsadmin)
        resp = MessagingResponse()
        reply = resp.message('Your wallet has been created! AI chatbot unlocked! Text "commands" to learn more.')

    # User needs help
    elif str(body.lower()) == 'commands' or str(body.lower()) == 'commands ':
        resp = MessagingResponse()
        reply = resp.message('Text anything to chat\nText "balance" to view wallet\nText "send <number> $<amount>" to transfer money\nSend image of QR code to decode\nText "$<amount>" to create invoice\nText BOLT11 invoice to decode')

    # TODO: SUPPORT LNURL
        # Send dashingoption@walletofsatoshi.com $21 (definitely possible, but might require another API)
        # Request dashingoption@walletofsatoshi.com $21 (need to associate phone number and lightning address)
    # User wants to pay a peer using a phone number and with no invoice send
        # Send 19095555555 $21
        # Request 19095555555 $21
        # Must be number that twilio can text otherwise funds cannot be extracted (try twilio first; on exception reply with error regarding number)

    # User sends money (Example: "Send 19095555555 $21")
    elif "send" in str(body.lower()) and "$" in str(body):
        # Extract "to number" and "amount" from body
        to_number, amount = extract_numbers_and_amounts(str(body))

        # Check balance
        balance = getbalance(lnbitsadmin)
        balance_sats = int(balance['balance']/1000)
        
        # Conversion to USD
        convert = str(btctousd(balance_sats)['USD'])
        index = convert.index('.')
        balanceUSD = convert[:index+3]

        if amount > balanceUSD:
            # Message user
            resp = MessagingResponse()
            reply = resp.message(f'Your request to send ${amount} exceeds balance of ${balanceUSD}.')
        else:
            # Find friend in database
            try:
                item = get_from_dynamodb(to_number)
                # "from_number" must be saved to extracted numbers database as latest "payee" for future use
                update_dynamodb(to_number, 'payee', from_number)

                # Get keys for invoice generation
                recipients_keys = item['lnbitsadmin']

                # Convert dollars to sats
                satsamount = usdtobtc(amount)['sats']
                # Generate offer invoice for recipient
                output = receiveinvoice(satsamount, "", recipients_keys)
                offer = output[0]
                offer_hash = output[1]

                # Save as to_number's offer
                update_dynamodb(to_number, 'offer', offer)
                # Save as to_number's offer_hash
                update_dynamodb(to_number, 'offer_hash', offer_hash)

                # Message friend
                message = f'You have been sent ${amount} in bitcoin from {from_number}. Text "Receive" to accept.'
                smstext(to_number, message, None)

                # Message user
                resp = MessagingResponse()
                reply = resp.message(f'${amount} offer sent to {to_number}.')

            # If not in database run exception
            except:
                # Message user about exception
                resp = MessagingResponse()
                reply = resp.message(f'{to_number} not in network. Text "invite" to bring friends in.')

    # User intends to receive funds
    elif str(body.lower()) == "receive" or str(body.lower()) == "receive ":
        # Extract payee and offer amount from database
        recipient_data = get_from_dynamodb(from_number)
        payee = recipient_data['payee']
        offer = recipient_data['offer']
        offer_hash = recipient_data['offer_hash']
        offer_amount = str(decodeinvoice(offer, lnbitsadmin)[0])

        # Get "payee" keys from database
        payee_data = get_from_dynamodb(payee)
        payee_keys = payee_data['lnbitsadmin']
        
        # Pay invoice with "payee" keys
        # Open subprocess to pay
        subprocess.Popen(["python", "payinvoice.py", offer, payee_keys, payee])
        # Open subprocess to see if message gets paid
        subprocess.Popen(["python", "checkinvoice.py", offer_hash, from_number, offer_amount, lnbitsadmin])
        
        # Reply to user
        resp = MessagingResponse()
        reply = resp.message('In process...')

    # If "receive" and new number then it sends terms and requires reply of "accept and receive"
    # If "accept and receive"...
        # creates wallet for new number
        # saves keys
        # creates invoice
        # "payee" keys used to pay invoice
    # If "receive" and database number then generates invoice for friend of amount and user pays friends wallet
    # If "request" and new number, return error because the friend for sure has no funds since new account (invite?)
    # If "request" and database number, then saves invoice to friend "lninvoice" and texts friend the pay message

    # Generate lightning invoice
    elif str(body) != "" and (str(body)[0] == '$' or isinstance(body, (int, float))):
        if str(body)[0] == '$':
            body = body[1:]
        # Convert input into sats
        sats = usdtobtc(body)['sats']
        memo = 'SMS Bot'

        # Create receive invoice
        output = receiveinvoice(sats,memo,lnbitsadmin)
        lninvoice = output[0]
        payment_hash = output[1]
        
        # Create QR code
        file = create_qrcode(lninvoice, filename='lightning.jpeg')

        # Start our TwiML response
        resp = MessagingResponse()
        # Send lightning invoice
        reply = resp.message(lninvoice)

        # Add a picture message (.jpg, .gif)
        # Make the HEAD request
        media_url = 'https://chatbtc.herokuapp.com/dev'
        response = requests.head(media_url)

        # Print the Content-Type to verify for Twilio
        # print(response.headers['Content-Type'])
        reply.media(media_url)

        # Open subprocess to see if message gets paid
        subprocess.Popen(["python", "checkinvoice.py", payment_hash, from_number, str(body), lnbitsadmin])
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

    # Decode an invoice from lightning invoice string
    elif len(body) > 4 and body[0:4] == 'lnbc':
        # Decode invoice
        decode = decodeinvoice(body, lnbitsadmin)

        # Save to User's AWS
        update_dynamodb(from_number, 'lninvoice', body)

        # Start our TwiML response
        resp = MessagingResponse()

        if decode[2] != "":
        # TODO: decode[2] shows "SMS wallet bot" instead of lightning memo
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

            # For Cashapp QR Codes
            if content.startswith("bitcoin:") or content.startswith("lightning="):
                parsed_url = urlparse(content)
                query_params = parse_qs(parsed_url.query)
                content = query_params.get('lightning', [None])[0]
            print('QR Decoded: ', content)

            if len(content) > 4 and content.lower()[0:4] == "lnbc":
                # Decode invoice
                decode = decodeinvoice(content, lnbitsadmin)

                # Save to User's AWS
                update_dynamodb(from_number, 'lninvoice', content)

                # Start our TwiML response
                resp = MessagingResponse()

                if decode[2] != "":
                # TODO: decode[2] shows "SMS wallet bot" instead of lightning memo
                    text = f'Text "pay" to send ${decode[0]} for {decode[2]}'
                else:
                    text = f'Text "pay" to send ${decode[0]}'
                
                reply = resp.message(text)

            else:
                # Start our TwiML response
                resp = MessagingResponse()
                reply = resp.message(content)

    # Pay invoice
    # TODO: consider making a password so that nobody can pay but your number and password combo
    elif str(body.lower()) == 'pay' or str(body.lower()) == 'pay ':
        # Get lninvoice
        item = get_from_dynamodb(from_number)
        lninvoice = item['lninvoice']

        # Open subprocess to pay
        subprocess.Popen(["python", "payinvoice.py", lninvoice, lnbitsadmin, from_number])
        status = 'In process...'

        # Start our TwiML response
        resp = MessagingResponse()
        reply = resp.message(status)

    elif 'weather' in str(body.lower()):
            location = extract_location(body)
            lat, lon = get_coordinates(location)
            weather = get_weather(lat,lon)
            current_weather = weather['current']
            # Open subprocess to allow ChatGPT time to think
            prompt = f'Answer the following question given the following data. Do your best and assume that the data is accurate and current for the location given in the question./nQuestion: {body}/nData:{current_weather}'
            subprocess.Popen(["python", "chatbot.py", prompt, from_number])
            resp = 'Thinking...' # Need these to return 'str(resp)' for higher level sms_reply() function

    # All else assumes prompt for bot
    else:
        # Open subprocess to allow ChatGPT time to think
        subprocess.Popen(["python", "chatbot.py", body, from_number])
        resp = 'Thinking...' # Need these to return 'str(resp)' for higher level sms_reply() function

    return str(resp)

if __name__ == "__main__":
    app.run(debug=True)