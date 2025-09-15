from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import Response

from app.weatherly import WeatherlyAppWrapper
from weather.cache import LocalCache

app: FastAPI = WeatherlyAppWrapper(cache=LocalCache())

START_ADDRESS: str = "20 W 34th St., New York, NY 10001"
END_ADDRESS: str = "1800 Walnut St, Philadelphia, PA 19103"
DAYS: int = 3


def test_get_weather_daily():
    client = TestClient(app)
    response: Response = client.get(f"/weather/daily/{START_ADDRESS}/{DAYS}")
    assert response.status_code == 200


def test_get_driving_report():
    client = TestClient(app)
    response: Response = client.get(f"/weather/drive/{START_ADDRESS}/{END_ADDRESS}")
    assert response.status_code == 200
