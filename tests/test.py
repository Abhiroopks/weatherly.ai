from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import Response

from app.weatherly import WeatherlyAppWrapper
from weather.cache import LocalCache

app: FastAPI = WeatherlyAppWrapper(cache=LocalCache())

START_ADDRESS: str = "20 W 34th St., New York, NY 10001"
END_ADDRESS: str = "1800 Walnut St, Philadelphia, PA 19103"
DAYS: int = 3
HOURS: int = 8


def test_get_current_weather():
    """
    Tests that the GET /weather/current/{address} endpoint returns a 200 status code.

    This test is responsible for ensuring that the current weather data can be retrieved
    successfully from the API.

    The test uses the FastAPI TestClient to make a GET request to the endpoint with the
    address as a path parameter. The response is then asserted to have a status code of 200.

    Args:
        None

    Returns:
        None
    """
    client = TestClient(app)
    response: Response = client.get(f"/weather/current/{START_ADDRESS}")
    assert response.status_code == 200


def test_get_weather_daily():
    """
    Tests that the GET /weather/daily/{address}/{days} endpoint returns a 200 status code.

    This test is responsible for ensuring that the daily weather data can be retrieved
    successfully from the API.

    The test uses the FastAPI TestClient to make a GET request to the endpoint with the
    address and number of days as path parameters. The response is then asserted to have a
    status code of 200.
    """
    client = TestClient(app)
    response: Response = client.get(f"/weather/daily/{START_ADDRESS}/{DAYS}")
    assert response.status_code == 200


def test_hourly():
    """
    Tests that the GET /weather/hourly/{address}/{hours} endpoint returns a 200 status code.

    This test is responsible for ensuring that the hourly weather data can be retrieved
    successfully from the API.

    The test uses the FastAPI TestClient to make a GET request to the endpoint with the
    address and number of hours as path parameters. The response is then asserted to have a
    status code of 200.
    """
    client = TestClient(app)
    response: Response = client.get(f"/weather/hourly/{START_ADDRESS}/{HOURS}")
    assert response.status_code == 200
