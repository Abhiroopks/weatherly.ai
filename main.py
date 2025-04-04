from fastapi import FastAPI
from geopy.geocoders import Nominatim

from directions.directions import get_directions, split_directions
from directions.models import Coordinates
from weather.models import Weather
from weather.weather import get_weather


app = FastAPI()
GEOLOCATOR = Nominatim(user_agent="CommuteSense", timeout=10)


@app.get("/")
def read_root() -> dict[str, str]:
    """
    Root endpoint of the API.

    Returns a JSON object with a single key-value pair: {"Hello": "World"}.
    """
    return {"Hello": "World"}


@app.get("/weather_report")
def get_weather_report(start_address: str, end_address: str) -> list[Weather]:
    """
    Endpoint to get weather report for a route defined by starting and ending coordinates.

    Args:
        start_address (str): The starting address of the route.
        end_address (str): The ending address of the route.

    Returns:
        list[Weather]: A list of Weather objects containing the weather information
            for each significant point along the route.
    """
    start_address = GEOLOCATOR.geocode(start_address)
    end_address = GEOLOCATOR.geocode(end_address)
    start_coord = Coordinates((start_address.latitude, start_address.longitude))
    end_coord = Coordinates((end_address.latitude, end_address.longitude))
    directions = get_directions(start_coord, end_coord)
    geo_points = split_directions(directions, interval=2000)
    weather_data = get_weather(geo_points)
    return weather_data
