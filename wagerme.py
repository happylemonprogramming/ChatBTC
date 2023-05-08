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

# TODO: 
'''
need to create virtual environment
need to pip install flask and twilio and other base requirements (check samule unicorn?)
need to create requirements.txt
need to create git repository
need to add, commit and post to GitHub
need to link heroku to GitHub
code->git->GitHub->heroku->twilio->phone number
phone number->twilio->heroku
'''

from flask import Flask, request, redirect, render_template, jsonify
from twilio.twiml.messaging_response import MessagingResponse
import os
import json

app = Flask(__name__)
# Should be an environmental variable
app.config["SECRET_KEY"] = os.environ.get('flasksecret')

@app.route("/sms", methods=['GET', 'POST'])
def sms_reply():
    """Respond to incoming calls with a simple text message.
        Example JSON
        JSON Body = {"name": "lemon", "tonality": "spicy", "influencer": "vanilla ice",
        "imgurl":"aws.lemonissosmart.com/img", "tags": "pickle bananas chimpanzees"}"""
    # Start our TwiML response
    resp = MessagingResponse()

    # Add a message
    resp.message("The Robots are coming! Head for the hills!")

    # Add a picture message
    resp.media(
        "https://farm8.staticflickr.com/7090/6941316406_80b4d6d50e_z_d.jpg"
    )

    return str(resp)

if __name__ == "__main__":
    app.run(debug=True)