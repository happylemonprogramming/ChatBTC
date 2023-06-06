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
TODO: make sure international numbers work

wallet
give banking to all SMS users
TODO: add discord
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
import datetime

openai.api_key = os.environ["openaiapikey"]
# phone_number = os.environ['phone_number']

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get('flasksecret')

@app.route("/error", methods=['GET', 'POST'])
def error_reply():
    # Default Twilio Option: https://demo.twilio.com/welcome/sms/reply
    # Start our TwiML response
    resp = MessagingResponse()
    reply = resp.message('Error, try again later :(')
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
    # Get the message the user sent our Twilio number
    body = request.values.get('Body', None)
    from_number = request.values.get('From', None)
    num_media = int(request.values.get('NumMedia', 0))
    wagerbot = get_from_dynamodb('wagerbot')

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

    print(user, type(user), body, type(body))

    # Service agreement
    if not user and str(body.lower().strip()) != 'accept':
    # if user == None and (body.lower() != 'accept' or body.lower() != "accept "):
        # Start our TwiML response

        resp = MessagingResponse()
        reply = resp.message('Thanks for using the bot!\U0001F916\nThis bot allows users to access AI and Bitcoin, but is experimental so use at your own risk. Text "accept" to acknowledge that this service is in beta and not reponsible for any lost funds or responses provided by the AI service.')

    # User accepts terms
    elif not user and str(body.lower().strip()) == 'accept':
    # elif type(body) is str and (body.lower() == 'accept' or body.lower() == "accept ") and user == None:
        wallet_data = createwallet(from_number)
        lnbitsadmin = wallet_data['adminkey']
        save_to_dynamodb(from_number, lnbitsadmin)
        resp = MessagingResponse()
        reply = resp.message('Your wallet has been created!\U0001F4B0\nAI chatbot unlocked!\U0001F916\nText "commands" to learn more.')

    # User needs help
    elif str(body.lower().strip()) == 'commands':
        resp = MessagingResponse()
        reply = resp.message('Text anything to chat\nText "balance" to view wallet\nText "send <number> $<amount>" to transfer money\nText "bet <number> $<amount> to wager\nSend image of QR code to decode\nText "$<amount>" to create invoice\nText lightning invoice to decode')

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
    elif str(body.lower().strip()) == 'receive':
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
        if str(body)[0] == '$' or '.' in str(body):
            body = body[1:]
            # Convert input into sats
            sats = usdtobtc(body)['sats']
            memo = 'SMS Bot (USD)'
        else:
            sats = body
            memo = 'SMS Bot (sats)'

        # Create receive invoice
        output = receiveinvoice(sats,memo,lnbitsadmin)
        lninvoice = output[0]
        payment_hash = output[1]
        
        # Create QR code
        create_qrcode(lninvoice, filename='lightning.jpeg')

        # Start our TwiML response
        resp = MessagingResponse()
        # Send lightning invoice
        reply = resp.message(lninvoice)

        # Add a picture message (.jpg, .gif)
        # Make the HEAD request
        media_url = 'https://chatbtc.herokuapp.com/dev'
        requests.head(media_url)

        # Print the Content-Type to verify for Twilio
        # print(response.headers['Content-Type'])
        reply.media(media_url)

        # Open subprocess to see if message gets paid
        subprocess.Popen(["python", "checkinvoice.py", payment_hash, from_number, str(body), lnbitsadmin])
        return str(resp)
    
    # Check wallet balance
    elif str(body.lower().strip()) == 'balance': #Autocorrect adds space
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
    elif str(body.lower().strip()) == 'pay':
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
            # Get weather data
            location = extract_location(body)
            lat, lon = get_coordinates(location)
            weather = get_weather(lat,lon)
            current_weather = weather['current']
            sunrise = datetime.datetime.utcfromtimestamp(current_weather['sunrise'])
            sunset = datetime.datetime.utcfromtimestamp(current_weather['sunset'])
            feels_likeC = round(float(current_weather['feels_like'])-273.15,2)
            feels_likeF = round((9/5)*(feels_likeC)+32.00,2)
            humidity = current_weather['humidity']
            cloudiness = current_weather['clouds']
            wind_speed_metric = round(float(current_weather['wind_speed']),2)
            wind_speed_imperial = round(wind_speed_metric*2.236936, 2)
            description = current_weather['weather'][0]['description'].title()

            # Compose text
            text = f'Weather for {location}\nDescription: {description}\nFeels Like: {feels_likeC}C ({feels_likeF}F)\nCloudiness: {cloudiness}%\nSunrise: {sunrise}\nSunset: {sunset}\nHumidity: {humidity}%\nWind Speed: {wind_speed_metric}m/s ({wind_speed_imperial}mph)'
            
            # Start our TwiML response
            resp = MessagingResponse()
            reply = resp.message(text)

            # # Open subprocess to allow ChatGPT time to think
            # prompt = f'Explain this data as concisely as possible (limiting the number of words in the reply) in a conversational tone and convert any relevant units into metric and imperial: {current_weather}'
            # subprocess.Popen(["python", "chatbot.py", prompt, from_number])
            # resp = 'Thinking...' # Need these to return 'str(resp)' for higher level sms_reply() function

# ##################################################################################
    # User wants to place a bet
    elif 'bet' in str(body.lower()):
        # EXAMPLE: "I bet 19095555555 $5 that Heat wins the NBA Championship"
        opponent, amount = extract_numbers_and_amounts(body)

        # Check balance
        balance = getbalance(lnbitsadmin)
        balance_sats = int(balance['balance']/1000)
        fee_sats = 50
        
        # Conversion to USD
        feeUSD = str(btctousd(fee_sats))
        convert = str(btctousd(balance_sats)['USD'])
        index = convert.index('.')
        balanceUSD = convert[:index+3]

        if amount >= balanceUSD:
            # Message user
            resp = MessagingResponse()
            reply = resp.message(f'Your request to send ${amount} exceeds balance of ${balanceUSD} with ${feeUSD} fee.\U0001F61E\n')

        else:
            # Add bet to database
            update_dynamodb('wagerbot', 'bet', body)
            update_dynamodb('wagerbot', 'amount', amount)
            update_dynamodb('wagerbot', 'bettor', from_number)
            update_dynamodb('wagerbot', 'opponent', opponent)

            # Get bot info
            wagerbot = get_from_dynamodb('wagerbot')
            print(wagerbot)

            # # Notify opponent
            # smstext(opponent, f"{body}\n\nReply 'Challenge' to take on the bet against {from_number}", media_url=None)

            # Notify opponent
            smstext(opponent, f"{body}\n\nReply 'Wager ${amount}' to take on the bet against {from_number}", media_url=None)

            # Confirmation
            resp = MessagingResponse()
            reply = resp.message('Opponent notified \U00002705')

    # Opponent wants to wager
    elif 'wager' in str(body.lower()):
        
        # If user is opponent
        if wagerbot['opponent'] == from_number:         
            # Bot information from database
            botkeys = wagerbot['lnbitsadmin']
            amountUSD = wagerbot['amount']
            bet = wagerbot['bet']
            
            # Conversion
            satsamount = usdtobtc(amountUSD)['sats']  # Convert dollars to sats

            # Invoice from Wagerbot for Opponent
            output1 = receiveinvoice(satsamount,bet,botkeys)
            lninvoice1 = output1[0]
            payment_hash1 = output1[1]

            # Get opponent keys to pay invoice
            opponent = get_from_dynamodb(from_number)
            opponentkeys = opponent['lnbitsadmin']

            # Opponent pay invoice
            subprocess.Popen(["python", "payinvoice.py", lninvoice1, opponentkeys, from_number]) #invoice, admin, number

            # Send confirmation
            resp = MessagingResponse()
            reply = resp.message('CHALLENGE ACCEPTED! \U0001F525') # fire emoji

            # Open subprocess to see if message gets paid
            subprocess.Popen(["python", "checkinvoice.py", payment_hash1, from_number, amountUSD, botkeys]) #hash, number, amount, admin


            # Invoice from Bot for Bettor
            output2 = receiveinvoice(satsamount,bet,botkeys)
            lninvoice2 = output2[0]
            payment_hash2 = output2[1]

            # Get bettor keys to pay invoice
            bettor_number = wagerbot['bettor']
            bettor = get_from_dynamodb(bettor_number)
            bettorkeys = bettor['lnbitsadmin']

            # Bettor pay invoice
            subprocess.Popen(["python", "payinvoice.py", lninvoice2, bettorkeys, bettor_number])

            # Notify Bettor
            smstext(bettor_number,'CHALLENGE ACCEPTED! \U0001F525', media_url=None)

            # Double check invoice is paid
            subprocess.Popen(["python", "checkinvoice.py", payment_hash2, bettor_number, amountUSD, botkeys])
        else:
            # Limit to 1 bet for now
            resp = MessagingResponse()
            reply = resp.message('Challenge unavailable \U0001F6AB')

    # Friend wants to wager
    elif str(body.lower().strip()) == 'challenge':
        # need to create a singular wallet with 1 set of keys
        # money deposited there will be withdrawn at conclusion
        # need database for: bet (string), bettor (string), challenger (list), initial amount (float), total amount (float)
        # if from_number not in challenger list: add them, invoice involved parties from singular wallet

        # Get bot info
        wagerbot = get_from_dynamodb('wagerbot')
        print(wagerbot)
        if wagerbot['opponent'] == from_number:         
            # Create receive invoice
            lnbitsadmin = wagerbot['lnbitsadmin']
            amountUSD = wagerbot['amount']
            bet = wagerbot['bet']
            satsamount = usdtobtc(amountUSD)['sats']  # Convert dollars to sats

            # Invoice for Opponent
            output1 = receiveinvoice(satsamount,bet,lnbitsadmin)
            lninvoice1 = output1[0]
            payment_hash1 = output1[1]
            
            # Start our TwiML response
            resp = MessagingResponse()
            # Send lightning invoice
            reply = resp.message(lninvoice1)
            # Send instruction
            smstext(from_number, f"Deposit wager at address to play", media_url=None)
            # Open subprocess to see if message gets paid
            subprocess.Popen(["python", "checkinvoice.py", payment_hash1, from_number, amountUSD, lnbitsadmin])

            # Invoice for Bettor
            output2 = receiveinvoice(satsamount,bet,lnbitsadmin)
            lninvoice2 = output2[0]
            payment_hash2 = output2[1]
            # Notify bettor
            bettor = wagerbot['bettor']
            # Send lightning invoice
            smstext(bettor, lninvoice2, media_url=None)
            # Send instruction
            smstext(bettor, f"Deposit wager at address to play", media_url=None)
            # Open subprocess to see if message gets paid
            subprocess.Popen(["python", "checkinvoice.py", payment_hash2, bettor, amountUSD, lnbitsadmin])
        else:
            # Limit to 1 bet for now
            resp = MessagingResponse()
            reply = resp.message('Challenge unavailable \U0001F6AB')


    # TODO need to define homies prior
    elif str(body.lower().strip()) == 'defeat':
        # Get bot info
        wagerbot = get_from_dynamodb('wagerbot')
        bet = wagerbot['bet']
        opponent = wagerbot['opponent']
        wagerbotkeys = wagerbot['lnbitsadmin']
        bettor = wagerbot['bettor']
        # Get wallet balance (msats)
        balance = getbalance(wagerbotkeys)
        balance_sats = int(balance['balance']/1000)
        print(f'wagerbot balance: {balance_sats} sats')
        fees = 50
        withdraw_amount = int(balance_sats-fees)
        print(f'withdrawal: {withdraw_amount} sats')

        # If bettor admits defeat
        if from_number == bettor:
            # Bettor lost and must pay opponent
            # Generate invoice for opponent for full wallet amount less fees
            item = get_from_dynamodb(opponent)
            opponentkeys = item['lnbitsadmin']
            output = receiveinvoice(withdraw_amount,bet,opponentkeys)
            lninvoice = output[0]
            payment_hash = output[1]

            # Open subprocess to pay
            subprocess.Popen(["python", "payinvoice.py", lninvoice, wagerbotkeys, bettor])
            status = 'Better luck next time, loser \U0001F44E'

            # Start our TwiML response
            resp = MessagingResponse()
            reply = resp.message(status)
            smstext(opponent, f'You won ${amount}! \U0001F38A', media_url=None)

        # If challenger admits defeat
        elif from_number == opponent:
            # Opponent lost and must pay bettor
            # Generate invoice for opponent for full wallet amount less fees
            item = get_from_dynamodb(bettor)
            bettorkeys = item['lnbitsadmin']
            output = receiveinvoice(withdraw_amount,bet,bettorkeys)
            lninvoice = output[0]
            payment_hash = output[1]

            # Open subprocess to pay
            subprocess.Popen(["python", "payinvoice.py", lninvoice, wagerbotkeys, opponent])
            status = 'Better luck next time, loser \U0001F44E'

            # Start our TwiML response
            resp = MessagingResponse()
            reply = resp.message(status)
            amount = wagerbot['amount']
            smstext(bettor, f'You won ${amount}! \U0001F38A', media_url=None)

        # If another number attempts to text
        else:
            # Start our TwiML response
            resp = MessagingResponse()
            reply = resp.message('No bets active \U0001F6AB')


        # need to check bet database to see what bet they are in
        # what if they are in multiple bets? maybe search keywords to compare body to the bet?
        # if person in bet and keywords match bet and consensus, then distribute funds

##################################################################################
    # All else assumes prompt for bot
    else:
        # Open subprocess to allow ChatGPT time to think
        subprocess.Popen(["python", "chatbot.py", body, from_number])
        resp = 'Thinking...' # Need these to return 'str(resp)' for higher level sms_reply() function

    return str(resp)

if __name__ == "__main__":
    app.run(debug=True)