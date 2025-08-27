from ast import Tuple

from fastapi import FastAPI, HTTPException

from directions.directions import get_directions, split_directions
from directions.models import Coordinates, Directions
from geolocate import get_geo_from_address
from weather.models import Weather, WeatherReport
from weather.weather import generate_weather_report, get_weather

app = FastAPI()


@app.get("/")
def read_root() -> dict[str, str]:
    """
    Root endpoint of the API.

    Returns a JSON object with a single key-value pair: {"Hello": "World"}.
    """
    return {"Hello": "World"}


def _get_weather_report(
    start_address: str, end_address: str, use_cache: bool
) -> WeatherReport:
    """
    Generates a weather report for the given start and end addresses.

    Args:
        start_address: The starting address for the route.
        end_address: The ending address for the route.
        use_cache: Whether to use the cache when generating the weather report.

    Returns:
        WeatherReport: A WeatherReport object containing the weather details for the route.
    """
    try:
        start_geo: list[dict] = get_geo_from_address(start_address)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to geocode start address: {e}"
        )

    try:
        end_geo: list[dict] = get_geo_from_address(end_address)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to geocode end address: {e}"
        )

    start_city: str = start_geo["address"]["city"]
    start_state: str = start_geo["address"]["state"]
    end_city: str = end_geo["address"]["city"]
    end_state: str = end_geo["address"]["state"]

    start_coord = Coordinates(
        (start_geo["geometry"]["lat"], start_geo["geometry"]["lng"])
    )
    end_coord = Coordinates((end_geo["geometry"]["lat"], end_geo["geometry"]["lng"]))

    try:
        directions: Directions = get_directions(start_coord, end_coord)
        geo_points: list[Tuple[str, Coordinates]] = split_directions(directions)
        weather_data: list[Weather] = get_weather(geo_points, use_cache=use_cache)
        weather_report: WeatherReport = generate_weather_report(
            weather_data, start_city, start_state, end_city, end_state
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to generate weather report: {e}"
        )

    return weather_report


@app.get("/weather_report/{start_address}/{end_address}")
def get_weather_report(start_address: str, end_address: str) -> WeatherReport:
    """
    Generates a weather report based on the given start and end addresses.

    Args:
        start_address: The starting address for the route.
        end_address: The ending address for the route.

    Returns:
        WeatherReport: A WeatherReport object containing the weather details for the route.
    """
    return _get_weather_report(start_address, end_address, use_cache=True)
