import datetime as dt
import json

import requests
from flask import Flask, jsonify, request

# create your API token, and set it up in Postman collection as part of the Body section
API_TOKEN = "bad_t0k3n$%^&"
# you can get API keys for free here - https://api-ninjas.com/api/jokes
RSA_KEY = "Y9UQQGHJ2ZHS3T3Y8WVN3LWBY"

app = Flask(__name__)


def get_clothing_recommendation(temp_c, weather_conditions):
    if temp_c < 10:
        return "Носіть теплу куртку, шапку та рукавиці."
    elif temp_c < 20:
        return "Носіть светр або легку куртку."
    else:
        return "Можете одягати легкий одяг."


class InvalidUsage(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv["message"] = self.message
        return rv


def get_weather(token, requester_name, location, date):
    url = "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{location}/{date}"
    params = {
        "unitGroup": "metric",
        "key": RSA_KEY,
        "include": "temp,wind,humidity,pressure"
    }
    headers = {
        "X-Api-Key": RSA_KEY
    }
    response = requests.get(url.format(location=location, date=date), params=params, headers=headers)
    if response.status_code == requests.codes.ok:
        weather_data = response.json()
        return weather_data
    else:
        raise InvalidUsage("Failed to retrieve weather data", status_code=response.status_code)


@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@app.route("/")
def home_page():
    return "<p><h2>KMA HW1: Andrii Makarets.</h2></p>"


@app.route("/content/api/v1/integration/generate/1", methods=["POST"])
def weather_endpoint():
    start_dt = dt.datetime.now()
    json_data = request.get_json()

    if not all(key in json_data for key in ["token", "requester_name", "location", "date"]):
        raise InvalidUsage("Incomplete payload", status_code=400)

    token = json_data["token"]

    if token != API_TOKEN:
        raise InvalidUsage("Wrong API token", status_code=403)

    requester_name = json_data["requester_name"]
    location = json_data["location"]
    date = json_data["date"]

    weather_data = get_weather(token, requester_name, location, date)

    end_dt = dt.datetime.now()

    # Отримуємо дані з погоди
    weather_info = weather_data["days"][0]

    clothing_recommendation = get_clothing_recommendation(weather_info["temp"], weather_info["conditions"])

    # Формуємо новий словник з необхідними полями
    formatted_response = {
        "requester_name": requester_name,
        "timestamp": start_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "location": location,
        "date": date,
        "weather": {
            "temp_c": weather_info["temp"],
            "wind_kph": weather_info["windspeed"],
            "pressure_mb": weather_info["pressure"],
            "humidity": weather_info["humidity"],
            "clothing_recommendation": clothing_recommendation
        }
    }

    return jsonify(formatted_response)