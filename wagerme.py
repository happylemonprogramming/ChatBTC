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
import os

import os
import openai

openai.api_key = os.environ["openaiapikey"]

app = Flask(__name__)
# Should be an environmental variable
app.config["SECRET_KEY"] = os.environ.get('flasksecret')

@app.route("/sms", methods=['GET', 'POST'])
def sms_reply():
    """Send a dynamic reply to an incoming text message"""
    # Get the message the user sent our Twilio number
    body = request.values.get('Body', None)
    print(body)

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

    # Add a picture message
    reply.media(
        "https://media2.giphy.com/media/xT0GqjBCkO9BEiSEOk/giphy.gif"
    )

    return str(resp)

if __name__ == "__main__":
    app.run(debug=True)