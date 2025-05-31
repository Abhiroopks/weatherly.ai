import openmeteo_requests
# from openmeteo_sdk.WeatherApiResponse import WeatherApiResponse
import requests_cache
from retry_requests import retry

from directions.models import Coordinates
from weather.cache import WeatherDataCache
from weather.models import (IDEAL_TEMP_RANGE, WEATHER_COMFORT_WEIGHTS,
                                Weather, WeatherReport)

# from fastapi import HTTPException


# Setup the Open-Meteo API client with cache and retry on error.
CACHE_SESSION = requests_cache.CachedSession(".cache", expire_after=3600)
RETRY_SESSION = retry(CACHE_SESSION, retries=5, backoff_factor=0.2)
OPENMETEO = openmeteo_requests.Client(session=RETRY_SESSION)
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
WEATHER_CACHE = WeatherDataCache(redis_host="redis")


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
    weather_data: list[Weather], comfort_score: int
) -> str:
    """
    Generate a description for a WeatherReport based on the comfort score and weather data.

    This function takes a list of Weather objects and a comfort score and generates a description
    string representing the weather summary. The description is based on the comfort score and
    includes phrases that describe the weather conditions.

    Args:
        weather_data (list[Weather]): A list of Weather objects containing weather data.
        comfort_score (int): The comfort score calculated from the weather data.

    Returns:
        str: A string representing the weather summary and comfort score.
    """

    if comfort_score >= 80:
        description = "Perfect weather with "
    elif comfort_score >= 50:
        description = "Good weather with "
    elif comfort_score >= 20:
        description = "Fair weather with "
    else:
        description = "Poor weather with "

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
    if any(not weather.is_day for weather in weather_data):
        description += "and some nighttime driving"
    else:
        description += "and all daytime driving"

    return description


def generate_weather_report(weather_data: list[Weather]) -> WeatherReport:
    """
    Generate a WeatherReport from a list of Weather objects.

    This function takes a list of Weather objects and generates a WeatherReport object.
    The WeatherReport object contains the maximum precipitation, mean temperature, maximum wind gusts,
    minimum visibility, and day/night status over the given data points, as well as a calculated comfort
    score and description.

    Args:
        weather_data (list[Weather]): A list of Weather objects containing weather data.

    Returns:
        WeatherReport: A WeatherReport object containing the weather summary and comfort score.
    """

    # Find the max precipitation amongst the data points.
    # The value here is mm precip over a 15 mins time span.
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
    description: str = generate_weather_description(weather_data, comfort_score)
    weather_report = WeatherReport(
        max_precip=max_precip,
        mean_temp=mean_temp,
        max_gust=max_gust,
        min_visibility=min_visibility,
        is_day=is_day,
        comfort_score=comfort_score,
        description=description,
        weather_points=weather_data
    )

    return weather_report


def get_weather(locations: list[Coordinates]) -> list[Weather]:
    """
    Retrieves current weather data for each location in the given list of Coordinates.

    Args:
        locations (list[Coordinates]): A list of Coordinates objects for which to retrieve weather data.

    Returns:
        list[Weather]: A list of Weather objects, each containing current weather data for a location.
    """

    weather_data: list[Weather] = []

    # Go through each location and check if cache contains weather data.
    # If not, request weather data from OpenMeteo.
    for loc in locations:
        if WEATHER_CACHE.has_weather_data(loc):
            weather = WEATHER_CACHE.get_weather_data(loc)
            weather_data.append(weather)
        else:
            params = {
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
            weather = OPENMETEO.weather_api(WEATHER_URL, params=params)
            print(weather)
            weather_obj = Weather(weather[0])
            print(weather_obj)
            weather_data.append(weather_obj)
            # Add to cache.
            WEATHER_CACHE.add_weather_data(loc, weather_obj)

    return weather_data
