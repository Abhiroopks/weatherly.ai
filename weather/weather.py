import openmeteo_requests
from openmeteo_sdk.WeatherApiResponse import WeatherApiResponse
import requests_cache
from retry_requests import retry

from fastapi import HTTPException

from directions.models import Coordinates
from weather.models import Weather

# Setup the Open-Meteo API client with cache and retry on error.
CACHE_SESSION = requests_cache.CachedSession(".cache", expire_after=3600)
RETRY_SESSION = retry(CACHE_SESSION, retries=5, backoff_factor=0.2)
OPENMETEO = openmeteo_requests.Client(session=RETRY_SESSION)
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"

def get_weather(locations: list[Coordinates]) -> list[Weather]:
    """
    Fetches weather data for a list of geographical locations.

    Args:
        locations (list[Coordinates]): A list of Coordinates objects representing
            the geographical locations for which to retrieve weather data.

    Returns:
        list[Weather]: A list of Weather objects containing the weather information
            for each location, such as temperature, precipitation, and weather code.
    """

    params = {
        "latitude": [loc.lat for loc in locations],
        "longitude": [loc.lon for loc in locations],
        "current": ["temperature_2m", "precipitation", "weather_code"],
    }

    try:
        responses: list[WeatherApiResponse] = OPENMETEO.weather_api(
            WEATHER_URL, params=params
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get weather")
    
    return [Weather(response) for response in responses]


def main():
    params = {
        "latitude": 52.52,
        "longitude": 13.41,
        "current": ["temperature_2m", "precipitation", "weather_code"],
    }
    responses = OPENMETEO.weather_api(WEATHER_URL, params=params)

    # Process first location. Add a for-loop for multiple locations or weather models
    response = responses[0]
    print(f"Coordinates {response.Latitude()}°N {response.Longitude()}°E")
    print(f"Elevation {response.Elevation()} m asl")
    print(f"Timezone {response.Timezone()}{response.TimezoneAbbreviation()}")
    print(f"Timezone difference to GMT+0 {response.UtcOffsetSeconds()} s")

    # Current values. The order of variables needs to be the same as requested.
    current = response.Current()

    current_temperature_2m = current.Variables(0).Value()

    current_precipitation = current.Variables(1).Value()

    current_weather_code = current.Variables(2).Value()

    print(f"Current time {current.Time()}")

    print(f"Current temperature_2m {current_temperature_2m}")
    print(f"Current precipitation {current_precipitation}")
    print(f"Current weather_code {current_weather_code}")


if __name__ == "__main__":
    main()
