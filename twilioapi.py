from twilio.rest import Client
import requests
import os

# Environment variables
twilioaccountsid = os.environ["twilioaccountsid"]
twilioauthtoken = os.environ["twilioauthtoken"]
phone_number = os.environ['phone_number']

def smstext(body, media_url):
  client = Client(twilioaccountsid, twilioauthtoken)
  message = client.messages.create(
    from_='+19098940201',
    to=phone_number,
    body=body,
    media_url= media_url
  )

  # Print the Content-Type
  print(message.sid)
  print('Text Message Sent')


if __name__ == "__main__":
  body = 'yo dude'
  media_url = 'https://chatbtc.herokuapp.com/dev'
  print(smstext(body, media_url=None))