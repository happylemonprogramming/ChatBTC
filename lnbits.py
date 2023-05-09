import requests
import json
import os

lnbitsapikey = os.environ["lnbitsapikey"]
lnbitsadminkey = os.environ["lnbitsadminkey"]

# Get wallet balance (msats)
def getbalance():
    url = 'https://legend.lnbits.com/api/v1/wallet'
    api_key = lnbitsapikey

    headers = {
        'X-Api-Key': api_key
    }

    response = requests.get(url, headers=headers)

    return response.json()

# Check Invoice Status
def checkstatus(payment_hash):
    url = f"https://legend.lnbits.com/api/v1/payments/{payment_hash}"
    headers = {
        "X-Api-Key": lnbitsapikey,
        "Content-type": "application/json"
    }

    response = requests.get(url, headers=headers)
    return response.json()

# Conversion to USD
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

# Conversion to sats
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
def receiveinvoice(amount, memo):
    url = 'https://legend.lnbits.com/api/v1/payments'
    api_key = lnbitsapikey

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
    payment_request = response.json()['payment_request']
    payment_hash = response.json()['payment_hash']
    return payment_request, payment_hash

# Decode invoice
def decodeinvoice(address):
    url = "https://legend.lnbits.com/api/v1/payments/decode"

    data = {
        "data": address
    }

    headers = {
        "X-Api-Key": lnbitsapikey,
        "Content-type": "application/json"
    }

    response = requests.post(url, data=json.dumps(data), headers=headers)
    json_data = response.json()

    # Get list of keys
    keys_list = list(json_data.keys())

    # Variables of interest
    amount = int(json_data['amount_msat']/1000)
    amountUSD = round(btctousd(amount)['USD'],2)
    expiry = json_data['expiry']
    description = json_data['description']
    return amountUSD, amount, description, expiry

# Pay invoice
def payinvoice(address):
    url = "https://legend.lnbits.com/api/v1/payments"

    data = {
        "out": True,
        "bolt11": address
    }

    headers = {
        "X-Api-Key": lnbitsadminkey,
        "Content-type": "application/json"
    }

    response = requests.post(url, data=json.dumps(data), headers=headers)
    key_list = list(response.json().keys())
    if 'payment_hash' in key_list:
        return 'Success!'
    else:
        return response.json()['detail']

# # Create wallet (Doesn't work)
# def create_lnbits_wallet(api_key):
#     url = "https://legend.lnbits.com/lnbits/api/v1/wallets"
#     headers = {
#         "Content-Type": "application/json",
#         "X-Api-Key": api_key
#     }
#     data = {
#         "name": "testwallet"
#     }
#     response = requests.post(url, json=data, headers=headers)

#     if response.status_code == 201:
#         wallet = response.json()
#         print("New wallet created:")
#         print(f"ID: {wallet['id']}")
#         print(f"Name: {wallet['name']}")
#         print(f"Admin key: {wallet['adminkey']}")
#         print(f"Read key: {wallet['readkey']}")
#         return wallet
#     else:
#         print("Error: Failed to create wallet")
#         print(f"Status code: {response.status_code}")
#         print(f"Response: {response.text}")
#         return None

# api_key = lnbitsapikey
# wallet = create_lnbits_wallet(api_key)


if __name__ == "__main__":
    output = receiveinvoice(2, 'yo')
    address = output[0]
    hashyhash = output[1]

    new_output = checkstatus(hashyhash)
    print(new_output)