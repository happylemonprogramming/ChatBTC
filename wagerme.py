'''
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
code->git->GitHub->heroku->twilio->phone number
phone number->twilio->heroku
'''

from flask import Flask, request, redirect, render_template, jsonify
from twilio.twiml.messaging_response import MessagingResponse
import openai
import qrcode

import os
import requests
import json
import base64
import io

openai.api_key = os.environ["openaiapikey"]
lnbitsapikey = os.environ["lnbitsapikey"]

app = Flask(__name__)
# Should be an environmental variable
app.config["SECRET_KEY"] = os.environ.get('flasksecret')

@app.route("/sms", methods=['GET', 'POST'])
def sms_reply():
    # Get the message the user sent our Twilio number
    body = request.values.get('Body', None)
    print(body)
    """Generate a lightning invoice"""
    if body.isdigit():
        # Create receive address
        url = 'https://legend.lnbits.com/api/v1/payments'
        api_key = lnbitsapikey
        amount = body # replace <int> with the actual integer value
        memo = 'bet' # replace <string> with the actual string value

        data = {
            'out': False,
            'amount': amount,
            'memo': memo
        }

        headers = {
            'X-Api-Key': api_key,
            'Content-type': 'application/json'
        }

        response = requests.post(url, headers=headers, data=json.dumps(data))
        
        # Start our TwiML response
        resp = MessagingResponse()

        # Add a message
        print(response.json()['payment_request'])
        lnaddress = str(response.json()['payment_request'])
        reply = resp.message(lnaddress)

        # Create QR Code
        def QR_Code(data):
            # Generate QR Code
            img = qrcode.make(data)
            imgpath = "qrcode.png"
            img.save(imgpath)

            # Read the image file as binary data
            with open(imgpath, 'rb') as f:
                image_data = f.read()

            # # Generate QR Code
            # img = qrcode.make(data)

            # # Write the image data to a binary buffer
            # buf = io.BytesIO()
            # img.save(buf, format='PNG')
            # image_data = buf.getvalue()
            return image_data

        # Convert binary to URI that can be referenced as a HTML src
        def binary_to_webaddress(binary):
            # Encode the image data as base64
            encoded_image = base64.b64encode(binary).decode('utf-8')

            # Create a data URI scheme for the image
            data_uri = 'data:image/png;base64,' + encoded_image

            # Return the data URI scheme
            return data_uri

        # Execute functions
        binary = QR_Code(lnaddress)
        uri = binary_to_webaddress(binary)

        # Add a picture message (.jpg, .gif)
        reply.media(
            uri
        )

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

        # # Add a picture message (.jpg, .gif)
        # reply.media(
        #     "https://media2.giphy.com/media/xT0GqjBCkO9BEiSEOk/giphy.gif"
        # )

    return str(resp)

if __name__ == "__main__":
    app.run(debug=True)