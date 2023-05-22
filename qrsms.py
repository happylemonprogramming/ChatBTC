'''
CREATE method: make code->save code locally-->cloud.py (upload to s3 to get url)
READ method: if url, save locally->detect & decode->return lnaddress [doesn't work with S3 link]
'''

from pyzbar.pyzbar import decode
import qrcode
from PIL import Image, ImageEnhance
import cv2
import requests
import os
import time

# Generate QR Code
def create_qrcode(input, filename):
    img = qrcode.make(input)
    img.save(filename) #needs to be a hyperlink
    return filename, img

# Decode QR Code
def decode_image(image):
    # Use pyzbar to decode the image
    result = decode(image)
    
    if len(result):
        return result[0].data.decode("utf-8")
    else:
        return None

# Process the Image to Extract QR Code
def process_image(media_path):
    # Idenfity if URL
    if 'http' in media_path:
        # Fetch the image from the URL
        url = media_path
        response = requests.get(url)
        response.raise_for_status()

        # Save the image locally
        path = 'QRread.jpg'
        with open(path, 'wb') as f:
            f.write(response.content)

    # Assume local path
    else:
        path = media_path

    if os.path.exists(path):

        data = decode_image(Image.fromarray(cropped))
        sharp_factor = 1.0
        start = time.time()

        while data is None:
            # Open the image
            image = Image.open(path)

            # Create enhancer
            enhancer = ImageEnhance.Sharpness(image)

            # Enhance sharpness
            enhancer.enhance(sharp_factor).save(path)

            # Read the image
            frame = cv2.imread(path)

            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # Threshold the image to highlight QR codes
            _, thresh = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY)

            # Find contours in the thresholded image
            contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

            # Filter out small contours based on area
            contours = [cnt for cnt in contours if cv2.contourArea(cnt) > 2000]

            # If any contours are found
            if len(contours) > 0:
                # Find the largest contour
                cnt = max(contours, key=cv2.contourArea)
                
                # Find bounding rect for the contour
                x, y, w, h = cv2.boundingRect(cnt)
                
                # Crop the image to this bounding rect
                cropped = thresh[y:y+h, x:x+w]
            else:
                cropped = thresh 
                
            data = decode_image(Image.fromarray(cropped))
            sharp_factor += 1.0

            if time.time()-start > 60:
                break
    else:
        # Return response to Heroku
        data = 'File not present'
        print(data)

    # Decode and return string
    return data 

if __name__ == '__main__':
    # string = 'yo gangster thug g-meister'
    # create_qrcode(string,'test.jpeg')
    # path = 'https://api.twilio.com/2010-04-01/Accounts/AC4b0fd142453f208bb5f81b6b8e9f844d/Messages/MMd5da0e2cbd46af04483164983eb6ef40/Media/ME5fc5a75e30abd4c7a57b9413d18d8a7f'
    # path = r"C:\Users\clayt\Documents\Programming\ChatBTC\fileread.jpg"
    path = 'https://s3-external-1.amazonaws.com/media.twiliocdn.com/AC4b0fd142453f208bb5f81b6b8e9f844d/7fe353862cae739e35eef46bdff16ef7'
    print(process_image(path))