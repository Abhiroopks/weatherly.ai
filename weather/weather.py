import os
from typing import Tuple

import openmeteo_requests
import requests_cache
from openai import OpenAI
from openmeteo_sdk.WeatherApiResponse import WeatherApiResponse
from retry_requests import retry

from directions.models import Coordinates
from prompts import WEATHER_DESCRIPTION
from weather.cache import WeatherDataCache
from weather.models import (
    IDEAL_TEMP_RANGE,
    WEATHER_COMFORT_WEIGHTS,
    Weather,
    WeatherReport,
)

# Setup the Open-Meteo API client with cache and retry on error.
CACHE_SESSION = requests_cache.CachedSession(".cache", expire_after=3600)
RETRY_SESSION = retry(CACHE_SESSION, retries=5, backoff_factor=0.2)
OPENMETEO = openmeteo_requests.Client(session=RETRY_SESSION)
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
WEATHER_CACHE = WeatherDataCache(redis_host="redis")


# Setup the OpenAI API client.
OPENAI = OpenAI(
    api_key=os.getenv("OPENROUTER_AI_KEY"), base_url="https://openrouter.ai/api/v1"
)


def precipitation_score(max_precip: float) -> float:
    """
    Calculate a precipitation score based on the maximum precipitation rate.

    The score is determined by assessing the severity of precipitation.
    A higher score indicates more favorable precipitation conditions with less intense precipitation.

    Args:
        max_precip (float): The maximum precipitation rate recorded.

    Returns:
        float: A score representing the precipitation condition, where 100 indicates low precipitation,
        50 indicates moderate precipitation, and 0 indicates high precipitation.
    """
    # If no precipitation at all.
    if max_precip == 0:
        return 100

    # If precipitation is light (less than 3 mm/hr).
    elif max_precip * 4 < 3:
        return 50

    # If precipitation is moderate or heavy (greater than 3 mm/hr).
    else:
        return 0


def temperature_score(mean_temp: float) -> float:
    """
    Calculate a temperature score based on weather data.

    The score is determined by the average temperature value among the data points.
    A higher score indicates more favorable weather conditions with temperatures closer to the ideal range.

    Args:
        mean_temp (float): The average temperature value among the data points.

    Returns:
        float: A score representing the temperature level, where 100 indicates ideal temperatures,
        50 indicates temperatures that are not ideal but still acceptable, and 0 indicates unacceptable temperatures.
    """

    # If the average temperature is within the ideal range.
    if mean_temp > IDEAL_TEMP_RANGE[0] and mean_temp < IDEAL_TEMP_RANGE[1]:
        return 100

    # Below ideal range but above 5C.
    elif mean_temp < IDEAL_TEMP_RANGE[0] and mean_temp > 5:
        return 50

    # Above ideal range but below 28C.
    elif mean_temp > IDEAL_TEMP_RANGE[1] and mean_temp < 28:
        return 50

    # Too hot or too cold.
    else:
        return 0


def wind_score(max_gust: float) -> float:
    """
    Calculate a wind score based on the maximum wind gust.

    The score is determined by assessing the severity of wind gusts.
    A higher score indicates more favorable wind conditions with less intense gusts.

    Args:
        max_gust (float): The maximum wind gust value recorded in km/h.

    Returns:
        float: A score representing the wind condition, where 100 indicates low wind gusts,
        50 indicates moderate wind gusts, and 0 indicates high wind gusts.
    """

    if max_gust < 10:
        return 100
    elif max_gust < 20:
        return 50
    else:
        return 0


def visibility_score(min_visibility: float) -> float:
    """
    Calculate a visibility score based on the minimum visibility of weather data.

    The score is determined by comparing the minimum visibility to a threshold.
    A higher score indicates more favorable visibility conditions.

    Args:
        min_visibility (float): The minimum visibility value in meters.

    Returns:
        float: A score representing the visibility level, where 100 indicates ideal visibility,
        80 indicates acceptable visibility, 50 indicates moderate visibility, 20 indicates low visibility,
        and 0 indicates very low visibility.
    """
    if min_visibility > 5000:
        return 100
    elif min_visibility > 3000:
        return 80
    elif min_visibility > 1000:
        return 50
    elif min_visibility > 500:
        return 20
    else:
        return 0


def day_night_score(is_day: bool) -> float:
    """
    Calculate a score based on day or night condition.

    This function evaluates whether it is day or night and returns a score
    accordingly. A higher score indicates that it is daytime, while a lower
    score indicates nighttime.

    Args:
        is_day (bool): A boolean indicating if it is daytime.

    Returns:
        float: A score representing the day or night condition, where 100
        indicates daytime and 0 indicates nighttime.
    """

    if is_day:
        return 100
    else:
        return 0


def calculate_comfort_score(
    max_precip: float,
    mean_temp: float,
    max_gust: float,
    min_visibility: float,
    is_day: bool,
) -> int:
    """
    Calculate a comfort score based on various weather parameters.

    The comfort score is computed using weighted contributions from precipitation,
    temperature, wind, visibility, and day/night conditions. Each parameter is
    scored individually, and the overall comfort score is a weighted sum of these
    individual scores.

    Args:
        max_precip (float): Maximum precipitation value over a specified time span.
        mean_temp (float): Average temperature value.
        max_gust (float): Maximum wind gust value.
        min_visibility (float): Minimum visibility value.
        is_day (bool): Boolean indicating if it is daytime.

    Returns:
        int: A rounded integer representing the overall comfort score, where a
        higher score indicates more comfortable weather conditions.
    """

    comfort_score = (
        precipitation_score(max_precip) * WEATHER_COMFORT_WEIGHTS["precipitation"]
        + temperature_score(mean_temp) * WEATHER_COMFORT_WEIGHTS["apparent_temperature"]
        + wind_score(max_gust) * WEATHER_COMFORT_WEIGHTS["wind"]
        + visibility_score(min_visibility) * WEATHER_COMFORT_WEIGHTS["visibility"]
        + day_night_score(is_day) * WEATHER_COMFORT_WEIGHTS["day_night"]
    )

    return round(comfort_score)


def generate_weather_description(
    weather_data: list[Weather],
    comfort_score: int,
    start_city: str,
    start_state: str,
    end_city: str,
    end_state: str,
) -> str:
    """
    Generate a human-readable description of the weather conditions along a route.

    The description is generated using an LLM from OpenRouter.ai. If the LLM generation
    fails, it falls back to a manual generation based on parameters.

    Args:
        weather_data (list[Weather]): A list of Weather objects representing the
            weather conditions at points along the route.
        comfort_score (int): The overall comfort score of the route.
        start_city (str): The city of the starting location.
        start_state (str): The state of the starting location.
        end_city (str): The city of the ending location.
        end_state (str): The state of the ending location.

    Returns:
        str: A human-readable description of the weather conditions along the route.
    """
    description: str = ""

    content: str = WEATHER_DESCRIPTION.format(
        start_city, start_state, end_city, end_state, comfort_score, str(weather_data)
    )
    response = None
    try:
        response = OPENAI.chat.completions.create(
            model="openai/gpt-oss-20b:free",
            messages=[
                {
                    "role": "user",
                    "content": content,
                }
            ],
        )
        description = response.choices[0].message.content
    except Exception as e:
        print(f"Exception during LLM call: {e}")
        print(
            "Failed to generate weather description from LLM. Defaulting to manual generation."
        )

    if description:
        return description

    # Generate the description based on the all parameters.

    description += (
        f"The route from {start_city}, {start_state} to {end_city}, {end_state} has "
    )
    if comfort_score >= 80:
        description += "perfect conditions with "
    elif comfort_score >= 50:
        description += "good conditions with "
    elif comfort_score >= 20:
        description += "bad conditions with "
    else:
        description += "very bad conditions with "

    # Add precipitation description
    if max(weather.precipitation for weather in weather_data) > 0:
        description += "some precipitation, "

    # Add temperature description
    if comfort_score >= 50:
        description += "mild temperatures, "
    else:
        description += "uncomfortable temperatures, "

    # Add wind description
    if max(weather.wind_gusts for weather in weather_data) > 10:
        description += "strong winds, "
    else:
        description += "light winds, "

    # Add visibility description
    if min(weather.visibility for weather in weather_data) < 5000:
        description += "low visibility, "
    else:
        description += "good visibility, "

    # Add day/night description
    has_day: bool = any(weather.is_day for weather in weather_data)
    has_night: bool = any(not weather.is_day for weather in weather_data)
    if has_day and has_night:
        description += "and some day/night time driving"
    elif has_day and not has_night:
        description += "and all daytime driving"
    else:
        description += "and all nighttime driving"

    return description


def generate_weather_report(
    weather_data: list[Weather],
    start_city: str,
    start_state: str,
    end_city: str,
    end_state: str,
) -> WeatherReport:
    # Find the max precipitation amongst the data points.
    # The value here is mm precip over a 15 mins time span.
    """
    Generate a weather report for the given start and end addresses.

    Args:
        weather_data (list[Weather]): A list of Weather objects representing the
            weather conditions at points along the route.
        start_city (str): The city of the starting location.
        start_state (str): The state of the starting location.
        end_city (str): The city of the ending location.
        end_state (str): The state of the ending location.

    Returns:
        WeatherReport: A WeatherReport object containing the weather details for the route.
    """
    max_precip: float = max([weather.precipitation for weather in weather_data])

    # Calculate the average temperature over the data points.
    mean_temp: float = sum([weather.apparent_temp for weather in weather_data]) / len(
        weather_data
    )

    # Highest wind gust over the route.
    max_gust: float = max([weather.wind_gusts for weather in weather_data])

    # Lowest visibility over the route
    min_visibility: float = min([weather.visibility for weather in weather_data])

    # If any portion of the route is not day, then the route is night.
    is_day: bool = all([weather.is_day for weather in weather_data])

    comfort_score: int = calculate_comfort_score(
        max_precip, mean_temp, max_gust, min_visibility, is_day
    )
    description: str = generate_weather_description(
        weather_data, comfort_score, start_city, start_state, end_city, end_state
    )
    weather_report = WeatherReport(
        max_precip=max_precip,
        mean_temp=mean_temp,
        max_gust=max_gust,
        min_visibility=min_visibility,
        is_day=is_day,
        comfort_score=comfort_score,
        description=description,
    )

    return weather_report


def get_weather(
    locations: list[Tuple[str, Coordinates]], use_cache: bool = True
) -> list[Weather]:
    """
    Retrieve weather data for the given locations.

    This function takes a dictionary of geo_key to Coordinates objects and
    returns a dictionary of geo_key to Weather objects. It checks the cache
    first to see if the weather data is already available. If not, it requests
    the data from the OpenMeteo API and then caches it for later use.

    Args:
        locations (list[Tuple[str, Coordinates]]): A list of tuples consisting
        of geo_key and Coordinates objects.

        use_cache (bool, optional): Whether to use the cache. Defaults to True.

    Returns:
        dict[str, Weather]: A dictionary of geo_key to Weather objects.
    """
    weather_data: list[Weather] = []

    for geo_key, loc in locations:
        if use_cache and WEATHER_CACHE.has_weather_data(geo_key):
            weather_data.append(WEATHER_CACHE.get_weather_data(geo_key))
        else:
            params: dict = {
                "latitude": loc.lat,
                "longitude": loc.lon,
                "current": [
                    "apparent_temperature",
                    "precipitation",
                    "weather_code",
                    "is_day",
                    "wind_gusts_10m",
                    "visibility",
                ],
            }

            response: list[WeatherApiResponse] = OPENMETEO.weather_api(
                WEATHER_URL, params=params
            )

            weather_obj: Weather = Weather(response[0], geo_key=geo_key)
            weather_data.append(weather_obj)
            if use_cache:
                WEATHER_CACHE.add_weather_data(geo_key, weather_obj)

    return weather_data
