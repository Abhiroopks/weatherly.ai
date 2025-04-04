from fastapi import FastAPI

from directions.directions import get_directions, split_directions
from directions.models import Coordinates
from weather.models import Weather
from weather.weather import get_weather

app = FastAPI()


@app.get("/")
def read_root() -> dict[str, str]:
    """
    Root endpoint of the API.

    Returns a JSON object with a single key-value pair: {"Hello": "World"}.
    """
    return {"Hello": "World"}


@app.get("/weather_report")
def get_weather_report(
    start_lat: float, start_lon: float, end_lat: float, end_lon: float
) -> list[Weather]:
    """
    Endpoint to get weather report for a route defined by starting and ending coordinates.

    Args:
        start_lat: The starting latitude.
        start_lon: The starting longitude.
        end_lat: The ending latitude.
        end_lon: The ending longitude.

    Returns:
        list[Weather]: A list of Weather objects containing the weather information
            for each significant point along the route.
    """
    start = Coordinates((start_lat, start_lon))
    end = Coordinates((end_lat, end_lon))
    directions = get_directions(start, end)
    geo_points = split_directions(directions, interval=2000)
    weather_data = get_weather(geo_points)
    return weather_data
