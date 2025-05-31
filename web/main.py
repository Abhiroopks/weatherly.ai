from fastapi import FastAPI, HTTPException
from geopy.geocoders import Nominatim

from directions.directions import get_directions, split_directions
from directions.models import Coordinates
from weather.models import WeatherReport
from weather.weather import generate_weather_report, get_weather

app = FastAPI()
GEOLOCATOR = Nominatim(user_agent="CommuteSense", timeout=10)  # type: ignore


@app.get("/")
def read_root() -> dict[str, str]:
    """
    Root endpoint of the API.

    Returns a JSON object with a single key-value pair: {"Hello": "World"}.
    """
    return {"Hello": "World"}


@app.get("/weather_report")
def get_weather_report(start_address: str, end_address: str) -> WeatherReport:
    """
    Generates a weather report based on the given start and end addresses.

    Args:
        start_address: The starting address for the route.
        end_address: The ending address for the route.

    Returns:
        WeatherReport: A WeatherReport object containing the weather details for the route.
    """
    start_geo = GEOLOCATOR.geocode(start_address)
    if start_geo is None:
        raise HTTPException(status_code=400, detail=f"Invalid address: {start_address}")

    end_geo = GEOLOCATOR.geocode(end_address)
    if end_geo is None:
        raise HTTPException(status_code=400, detail=f"Invalid address: {end_address}")

    start_coord = Coordinates((start_geo.latitude, start_geo.longitude))  # type: ignore
    end_coord = Coordinates((end_geo.latitude, end_geo.longitude))  # type: ignore
    directions = get_directions(start_coord, end_coord)

    geo_points = split_directions(directions)

    weather_data = get_weather(geo_points)

    return generate_weather_report(weather_data)
