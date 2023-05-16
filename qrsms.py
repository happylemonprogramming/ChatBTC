'''TODO: Code is not currently utilized because current methods of MMS messages yield twilio error
CREATE method: make code->save code locally-->cloud.py (upload to s3 to get url)
READ method: if url, save locally->detect & decode->return lnaddress [doesn't work with S3 link]
'''
# Generate QR Code
import qrcode
from PIL import Image

def create_qrcode(input, filename):
    img = qrcode.make(input)
    img.save(filename) #needs to be a hyperlink
    return filename, img

# Read QR Code from Path
import cv2
import requests
import os

def read_qrcode(path):
    if 'http' in path:
        # Fetch the image from the URL
        path = url
        response = requests.get(url)
        response.raise_for_status()

        # Save the image locally
        path = 'fileread.png'
        with open(path, 'wb') as f:
            f.write(response.content)

    # Load the image
    print(path)
    if os.path.exists(path): 
        image = cv2.imread(path)

        # Initialize the cv2 QRCode detector
        detector = cv2.QRCodeDetector()

        # Detect and decode
        data, bbox, straight_qrcode = detector.detectAndDecode(image)

        # If there is a QR code
        if bbox is not None:
            print(f"QRCode data:\n{data}")
        else:
            print("QR Code not detected")
    else:
        print("File not present")
        return data


''' TODO: need to look more into this method
no server download required'''
# # Read QR Code ()
# import requests
# import numpy as np

# def read_qrcode(url):
#     # Download the image
#     resp = requests.get(url, stream=True).raw
#     image = np.asarray(bytearray(resp.read()), dtype="uint8")
#     img = cv2.imdecode(image, cv2.IMREAD_COLOR)

#     # Convert the image to grayscale
#     gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

#     # Detect QR codes within the image
#     qr_codes = decode(gray)
#     return qr_codes[0].data.decode('utf-8')

''' TODO: need to look more into this method
no server download required'''
# # Read QR Code from URL (BYTES METHOD)
# import requests
# from PIL import Image
# import numpy as np
# from io import BytesIO

# def read_qrcode(url):
#     # Fetch the image from the URL
#     response = requests.get(url)
#     response.raise_for_status()

#     # Open the image
#     img = Image.open(BytesIO(response.content))

#     # Convert the image to a numpy array so cv2 can use it
#     img_array = np.array(img)

#     # Convert RGB to BGR 
#     final_img = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)

#     # Initialize the cv2 QRCode detector
#     detector = cv2.QRCodeDetector()

#     # Detect and decode
#     data, bbox, straight_qrcode = detector.detectAndDecode(final_img)

#     # If there is a QR code
#     if bbox is not None:
#         print(f"QRCode data:\n{data}")
#     else:
#         print("QR Code not detected")

''' TODO: Couldn't get this method to work because of zbar errors with Aptfile
local location method'''
# # Read QR Code after download (PYZBAR METHOD)
# import cv2
# from pyzbar.pyzbar import decode

# def read_qrcode_local(path):
#     # Load the image
#     img = cv2.imread(path)

#     # Convert the image to grayscale
#     gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

#     # Detect QR codes within the image
#     qr_codes = decode(gray)
#     return qr_codes[0].data.decode('utf-8')

if __name__ == '__main__':
    url = 'yo dawg'
    # print(read_qrcode('lightning.jpeg'))
    create_qrcode(url,'lightning.jpeg')