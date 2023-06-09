import requests
import json
import os
from bs4 import BeautifulSoup
import re

lnbitsapikey = os.environ["lnbitsapikey"]
lnbitsadminkey = os.environ["lnbitsadminkey"]

# Get wallet balance (msats)
def getbalance(api_key):
    url = 'https://legend.lnbits.com/api/v1/wallet'
    # api_key = lnbitsapikey

    headers = {
        'X-Api-Key': api_key
    }

    response = requests.get(url, headers=headers)

    return response.json()

# Conversion to sats
def usdtobtc(amount):
    url = 'https://legend.lnbits.com/api/v1/conversion'

    headers = {
        'Content-Type': 'application/json'
    }

    data = {
        'from': 'usd',
        'amount': amount,
        'to': 'sat'
    }

    response = requests.post(url, headers=headers, json=data)
    return response.json()

# Conversion to USD
def btctousd(amount):
    url = 'https://legend.lnbits.com/api/v1/conversion'

    headers = {
        'Content-Type': 'application/json'
    }

    data = {
        'from': 'sat',
        'amount': amount,
        'to': 'usd'
    }

    response = requests.post(url, headers=headers, json=data)
    return response.json()

# Create receive address
def receiveinvoice(amount, memo, api_key):
    url = 'https://legend.lnbits.com/api/v1/payments'
    # api_key = lnbitsapikey

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

    try:
        payment_request = response.json()['payment_request']
        payment_hash = response.json()['payment_hash']
    except:
        payment_request, payment_hash = response.json()

    return payment_request, payment_hash

# Check Invoice Status
def checkstatus(payment_hash, api_key):
    url = f"https://legend.lnbits.com/api/v1/payments/{payment_hash}"
    headers = {
        "X-Api-Key": api_key,
        "Content-type": "application/json"
    }

    response = requests.get(url, headers=headers)
    return response.json()

# Decode invoice
def decodeinvoice(address, api_key):
    url = "https://legend.lnbits.com/api/v1/payments/decode"

    data = {
        "data": address
    }

    headers = {
        "X-Api-Key": api_key,
        "Content-type": "application/json"
    }

    response = requests.post(url, data=json.dumps(data), headers=headers)
    json_data = response.json()

    # Get list of keys
    keys_list = list(json_data.keys())

    # Variables of interest
    amount = int(json_data['amount_msat']/1000)
    # amountUSD = round(btctousd(amount)['USD'],2)
    amountUSD = "{:.2f}".format(float(btctousd(amount)['USD']))
    expiry = json_data['expiry']
    description = json_data['description']
    # TODO: amountUSD = $1.0

    return amountUSD, amount, description, expiry

# Pay invoice
def payinvoice(address, api_key):
    url = "https://legend.lnbits.com/api/v1/payments"

    data = {
        "out": True,
        "bolt11": address
    }

    headers = {
        "X-Api-Key": api_key,
        "Content-type": "application/json"
    }

    response = requests.post(url, data=json.dumps(data), headers=headers)
    key_list = list(response.json().keys())
    if 'payment_hash' in key_list:
        return 'Success!'
    else:
        return response.json()['detail']

def createwallet(from_number):
    # API call to create wallet
    response = requests.get(f'https://legend.lnbits.com/wallet?nme={from_number}', headers={'accept': 'text/html'})
    # Parse HTML output from API
    soup = BeautifulSoup(response.text, 'html.parser')
    # Find all script tags
    scripts = soup.find_all('script')

    # Iterate through scripts if multiple
    for script in scripts:
        # Find the script tag with the wallet data
        if script.string and 'window.wallet =' in script.string:
            # Extract the JSON string
            json_str = re.search(r'window\.wallet = ({.*?});', script.string).group(1)
            # Parse the JSON string into a Python dictionary
            wallet_data = json.loads(json_str)
            break
        else:
            wallet_data = 'ERROR'
    return wallet_data

if __name__ == "__main__":
    wager = 'wagerbot'
    wallet_data = createwallet(wager)
    adminkey = wallet_data['adminkey']
    print(adminkey)
