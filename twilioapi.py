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

  # Make the HEAD request
  response = requests.head(media_url)

  # Print the Content-Type
  print(response.headers['Content-Type'])
  print(message.sid)
  print('Text Message Sent')


if __name__ == "__main__":
  body = 'yo'
  media_url = 'https://lightningsms.s3.us-west-1.amazonaws.com/lightning.jpeg?AWSAccessKeyId=AKIAVIJP4GSVZCZH4NXY&Signature=jO%2F7Fyl%2B%2BLIjLsa3QsZHsH205Ts%3D&Expires=1684220724'
  print(smstext(body, media_url))