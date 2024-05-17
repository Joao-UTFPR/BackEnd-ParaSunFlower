import os

import requests


def get_wind_speeds(lat,lon):
    params = {"appid": os.getenv("open_weather_appid"), "exclude": "minutely,daily", "lat":lat, "lon":lon}
    response = requests.get(url="https://api.openweathermap.org/data/2.5/weather", params=params)
    json_resp = response.json()
    return json_resp.get("wind").get("speed")

if __name__ == "__main__":
    get_wind_speeds(-25.437689,-49.270484)