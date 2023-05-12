# Read QR Code
import cv2
from pyzbar.pyzbar import decode

def read_qrcode_local(path):
    # Load the image
    img = cv2.imread(path)

    # Convert the image to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Detect QR codes within the image
    qr_codes = decode(gray)
    return qr_codes[0].data.decode('utf-8')

# Generate QR Code
import qrcode
from PIL import Image

def create_qrcode(input, filename):
    img = qrcode.make(input)
    img.save(filename) #needs to be a hyperlink
    return filename

import requests
import numpy as np

def read_qrcode(url):
    # Download the image
    resp = requests.get(url, stream=True).raw
    image = np.asarray(bytearray(resp.read()), dtype="uint8")
    img = cv2.imdecode(image, cv2.IMREAD_COLOR)

    # Convert the image to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Detect QR codes within the image
    qr_codes = decode(gray)
    return qr_codes[0].data.decode('utf-8')


if __name__ == '__main__':
    path = r"C:\Users\clayt\Downloads\qr-code-bc94057f452f4806af70fd34540f72ad.png"
    read_qrcode(path)
    create_qrcode(path)