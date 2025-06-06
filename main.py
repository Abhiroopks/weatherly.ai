from fastapi import FastAPI, HTTPException
from opencage.geocoder import OpenCageGeocode

from directions.directions import get_directions, split_directions
from directions.models import Coordinates, Directions
from tools import get_key
from weather.models import Weather, WeatherReport
from weather.weather import generate_weather_report, get_weather

app = FastAPI()


OPENCAGE_KEY = get_key("opencage.key")
GEOLOCATOR = OpenCageGeocode(OPENCAGE_KEY)


@app.get("/")
def read_root() -> dict[str, str]:
    """
    Root endpoint of the API.

    Returns a JSON object with a single key-value pair: {"Hello": "World"}.
    """
    return {"Hello": "World"}


@app.get("/weather_report_from_coordinates/{start_lat}/{start_lon}/{end_lat}/{end_lon}")
def get_weather_report_from_coordinates(
    start_lat: float, start_lon: float, end_lat: float, end_lon: float
) -> WeatherReport:
    """
    Generates a weather report based on the given start and end coordinates.

    Args:
        start_lat: The starting latitude coordinate for the route.
        start_lon: The starting longitude coordinate for the route.
        end_lat: The ending latitude coordinate for the route.
        end_lon: The ending longitude coordinate for the route.

    Returns:
        WeatherReport: A WeatherReport object containing the weather details for the route.
    """
    start_coord = Coordinates((start_lat, start_lon))
    end_coord = Coordinates((end_lat, end_lon))

    try:
        directions: Directions = get_directions(start_coord, end_coord)

        geo_points: dict[str, Coordinates] = split_directions(directions)

        weather_data: dict[str, Weather] = get_weather(geo_points)

        weather_report: WeatherReport = generate_weather_report(
            list(weather_data.values())
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to generate weather report: {e}"
        )

    return weather_report


@app.get("/weather_report_from_addresses/{start_address}/{end_address}")
def get_weather_report_from_addresses(
    start_address: str, end_address: str
) -> WeatherReport:
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

    start_lat = start_geo[0]["geometry"]["lat"]
    start_lon = start_geo[0]["geometry"]["lng"]
    end_lat = end_geo[0]["geometry"]["lat"]
    end_lon = end_geo[0]["geometry"]["lng"]
    return get_weather_report_from_coordinates(start_lat, start_lon, end_lat, end_lon)
