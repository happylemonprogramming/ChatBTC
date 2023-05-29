import requests
import json
import os

api_key = os.environ["openweatherapikey"]

def get_weather(lat, lon):
    # https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&exclude={part}&appid={API key}
    base_url = "https://api.openweathermap.org/data/3.0/onecall"
    
    parameters = {
        "lat": lat,
        "lon": lon,
        "appid": api_key
    }
    
    response = requests.get(base_url, params=parameters)

    if response.status_code == 200:
        weather_data = response.json()
        # print(json.dumps(weather_data, indent=4))
        return weather_data
    else:
        print("Error:", response.status_code)

def get_coordinates(location):
    # http://api.openweathermap.org/geo/1.0/direct?q={city name},{state code},{country code}&limit={limit}&appid={API key}
    base_url = 'http://api.openweathermap.org/geo/1.0/direct'
    parameters = {
        "q": location,
        "appid": api_key,
        "limit": 1  # Number of responses
    }

    response = requests.get(base_url, params=parameters)

    if response.status_code == 200:
        coordinate = response.json()
        lat = coordinate[0]['lat']
        lon = coordinate[0]['lon']
        # print(json.dumps(coordinate, indent=4))
        return lat, lon
    else:
        print("Error:", response.status_code)

def extract_location(string):
    keywords = [' in ', ' at ']
    for keyword in keywords:
        if keyword in string:
            return string.split(keyword, 1)[1].strip().rstrip('?')


if __name__ == "__main__":

    string1 = "what's the weather like in kansas city?"
    string2 = "what is the temperature at mt. everest?"
    location = extract_location(string2)
    print(location)
    lat, lon = get_coordinates(location)
    print(lat,lon)
    weather = get_weather(lat,lon)
