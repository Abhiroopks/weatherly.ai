import os
from datetime import datetime, timedelta
from typing import Any

import openmeteo_requests
import pandas as pd
import requests_cache
from openai import OpenAI
from openmeteo_sdk.VariablesWithTime import VariablesWithTime
from openmeteo_sdk.WeatherApiResponse import WeatherApiResponse
from retry_requests import retry

from ai.chat import chat
from ai.prompts import DAILY_WEATHER_DESCRIPTION, WEATHER_DESCRIPTION
from models.core import Coordinate
from models.weather import (
    IDEAL_TEMP_RANGE,
    WEATHER_COMFORT_WEIGHTS,
    WMO_WEATHER_CODES,
    CurrentWeather,
    DailyWeather,
    DrivingReport,
)
from weather.cache import WeatherCache

# Number of days to forecast. Used in openmeteo API call.
FORECAST_DAYS: int = 7

# Setup the Open-Meteo API client with cache and retry on error.
CACHE_SESSION = requests_cache.CachedSession(".cache", expire_after=3600)
RETRY_SESSION = retry(CACHE_SESSION, retries=5, backoff_factor=0.2)
OPENMETEO = openmeteo_requests.Client(session=RETRY_SESSION)  # type: ignore
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
# cache = WeatherDataCache(redis_host="redis")


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


def generate_llm_daily_description(
    weather_data: list[DailyWeather], location: str
) -> str | None:
    """
    Generate a human-readable description of the weather conditions for the day using a
    language model.

    The description is generated by passing the weather data to a language model. The
    language model is expected to generate a human-readable description of the weather
    conditions for the days.

    Args:
        weather_data (list[DailyWeather]): A list of DailyWeather objects representing the
            weather conditions for numerous days, for a single location.

        location (str): The location corresponding to the weather data. Format is "{city}, {state}".

    Returns:
        str | None: A human-readable description of the weather conditions, or None if the
        description could not be generated.
    """

    content: str = DAILY_WEATHER_DESCRIPTION.format(location, weather_data)

    return chat(prompt=content)


def generate_llm_driving_description(
    comfort_score: int,
    start_city: str,
    start_state: str,
    end_city: str,
    end_state: str,
    weather_data: list[CurrentWeather],
) -> str | None:
    """
    Generate a human-readable description of the weather conditions along a route using a
    language model.

    The description is generated by passing the start and end addresses, along with the
    comfort score and weather data, to a language model. The language model is expected to
    generate a human-readable description of the weather conditions along the route.

    Args:
        comfort_score (int): The overall comfort score of the route.
        start_city (str): The city of the starting location.
        start_state (str): The state of the starting location.
        end_city (str): The city of the ending location.
        end_state (str): The state of the ending location.
        weather_data (list[CurrentWeather]): A list of CurrentWeather objects representing the
            weather conditions at points along the route.

    Returns:
        str | None: A human-readable description of the weather conditions along the route, or
            None if the language model fails to generate a description.
    """
    content: str = WEATHER_DESCRIPTION.format(
        start_city, start_state, end_city, end_state, comfort_score, weather_data
    )

    return chat(prompt=content)


def generate_weather_description_manually(
    weather_data: list[CurrentWeather],
    comfort_score: int,
    start_city: str,
    start_state: str,
    end_city: str,
    end_state: str,
) -> str:
    """
    Generate a human-readable description of the weather conditions along a route manually.

    The description is generated based on the comfort score, precipitation, temperature,
    wind, visibility, and day/night conditions of the route.

    Args:
        weather_data (list[CurrentWeather]): A list of CurrentWeather objects representing the
            weather conditions at points along the route.
        comfort_score (int): The overall comfort score of the route.
        start_city (str): The city of the starting location.
        start_state (str): The state of the starting location.
        end_city (str): The city of the ending location.
        end_state (str): The state of the ending location.

    Returns:
        str: A human-readable description of the weather conditions along the route.
    """
    description = ""
    # Generate the description manually.
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


def generate_weather_description(
    weather_data: list[CurrentWeather],
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
        weather_data (list[CurrentWeather]): A list of CurrentWeather objects representing the
            weather conditions at points along the route.
        comfort_score (int): The overall comfort score of the route.
        start_city (str): The city of the starting location.
        start_state (str): The state of the starting location.
        end_city (str): The city of the ending location.
        end_state (str): The state of the ending location.

    Returns:
        str: A human-readable description of the weather conditions along the route.
    """

    description: str | None = generate_llm_driving_description(
        comfort_score,
        start_city,
        start_state,
        end_city,
        end_state,
        weather_data=weather_data,
    )

    if description:
        return description

    print("LLM description generation failed, resorting to manual description.")

    return generate_weather_description_manually(
        weather_data,
        comfort_score,
        start_city,
        start_state,
        end_city,
        end_state,
    )


def generate_weather_report(
    weather_data: list[CurrentWeather],
    start: dict,
    end: dict,
) -> DrivingReport:
    start_city: str = start["address"]["city"]
    start_state: str = start["address"]["state"]
    end_city: str = end["address"]["city"]
    end_state: str = end["address"]["state"]

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
    weather_report = DrivingReport(
        max_precip=max_precip,
        mean_temp=mean_temp,
        max_gust=max_gust,
        min_visibility=min_visibility,
        is_day=is_day,
        comfort_score=comfort_score,
        description=description,
    )

    return weather_report


def get_daily_weather_report(
    cache: WeatherCache,
    city: str,
    state: str,
    loc: Coordinate,
    days: int = 1,
) -> dict[str, list[DailyWeather] | str]:
    prefix: str = "daily"

    weather_days: list[DailyWeather] = []

    # Loop through the given number of days and get the weather for each day.
    for day_offset in range(days):
        date: datetime = datetime.today() + timedelta(days=day_offset)
        date_str: str = date.strftime("%Y-%m-%d")
        full_prefix: str = f"{prefix}_{date_str}"
        # Check if the weather for this day is already in the cache.
        if cache.has_weather(full_prefix, loc):
            daily_weather: DailyWeather = cache.get_weather(full_prefix, loc)  # type: ignore
            weather_days.append(daily_weather)
        else:
            # If not in the cache, make an API call to get the weather.
            params: dict = {
                "latitude": loc.lat,
                "longitude": loc.lon,
                "daily": [
                    "weather_code",
                    "temperature_2m_max",
                    "temperature_2m_min",
                    "apparent_temperature_max",
                    "apparent_temperature_min",
                    "sunrise",
                    "sunset",
                    "precipitation_sum",
                    "wind_speed_10m_max",
                ],
                # Always pull 7 days, because we will cache and potentially use it later.
                "forecast_days": FORECAST_DAYS,
                "timezone": "auto",
            }

            response: list[WeatherApiResponse] = OPENMETEO.weather_api(
                WEATHER_URL, params=params
            )

            # Parse the API response into a list of DailyWeather objects.
            daily_weather_list: list[DailyWeather] = parse_daily_weather_api_response(
                response
            )

            # Find the DailyWeather object for the current day and add it to the list.
            for _daily_weather in daily_weather_list:
                if _daily_weather.date == date_str:
                    weather_days.append(_daily_weather)

            # Cache the weather for each day.
            for _day_offset in range(days):
                _daily_weather: DailyWeather = daily_weather_list[_day_offset]
                _date: datetime = datetime.today() + timedelta(days=_day_offset)
                _full_prefix: str = f"{prefix}_{_date.strftime('%Y-%m-%d')}"
                cache.add_weather(_full_prefix, loc, _daily_weather)

    description: str | None = generate_llm_daily_description(
        weather_days, f"{city}, {state}"
    )

    if description is None:
        description = "Failed to generate via LLM."

    return {"days": weather_days, "description": description}


def get_current_weather(locations: list, cache: WeatherCache) -> list[CurrentWeather]:
    weather_data: list[CurrentWeather] = []
    prefix: str = "current"

    for loc in locations:
        if cache.has_weather(prefix, loc):
            weather_data.append(cache.get_weather(prefix, loc))  # type: ignore
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

            current_weather: CurrentWeather = CurrentWeather(
                **parse_current_weather_api_response(response[0])
            )

            if current_weather is None:
                continue

            weather_data.append(current_weather)
            cache.add_weather(prefix, loc, current_weather)

    return weather_data


def parse_daily_weather_api_response(
    _response: list[WeatherApiResponse],
) -> list[DailyWeather]:
    """
    Parse the response from the OpenMeteo API and extract the daily weather data.

    Args:
        _response (list[WeatherApiResponse]): The response from the OpenMeteo API.

    Returns:
        list[DailyWeather]: A list of DailyWeather objects, one for each day in the API response.
    """
    output: list[DailyWeather] = []

    response: WeatherApiResponse = _response[0]

    # Extract the UTC offset from the API response.
    utc_offset: int = response.UtcOffsetSeconds()

    # Extract the daily weather data from the API response.
    daily: VariablesWithTime | None = response.Daily()
    if daily is None:
        return output

    # Extract the WMO weather codes from the API response.
    wmo_description: list[str] = [
        WMO_WEATHER_CODES[int(wmo_code)]
        for wmo_code in daily.Variables(0).ValuesAsNumpy()
    ]

    # Extract the maximum, minimum, apparent maximum and apparent minimum temperatures.
    max_temp: list[float] = daily.Variables(1).ValuesAsNumpy().tolist()
    min_temp: list[float] = daily.Variables(2).ValuesAsNumpy().tolist()
    max_apparent_temp: list[float] = daily.Variables(3).ValuesAsNumpy().tolist()
    min_apparent_temp: list[float] = daily.Variables(4).ValuesAsNumpy().tolist()

    # Extract the sunrise and sunset times.
    sunrise: list[str] = [
        datetime.fromtimestamp(ts + utc_offset).strftime("%I:%M %p")
        for ts in daily.Variables(5).ValuesInt64AsNumpy()
    ]
    sunset: list[str] = [
        datetime.fromtimestamp(ts + utc_offset).strftime("%I:%M %p")
        for ts in daily.Variables(6).ValuesInt64AsNumpy()
    ]

    # Extract the precipitation sum and maximum wind speed.
    precipitation_sum: list[float] = daily.Variables(7).ValuesAsNumpy().tolist()
    max_wind_speed: list[float] = daily.Variables(8).ValuesAsNumpy().tolist()

    # Extract the date from the API response.
    date = (
        pd.date_range(
            start=pd.to_datetime(daily.Time() + utc_offset, unit="s", utc=True),
            end=pd.to_datetime(daily.TimeEnd() + utc_offset, unit="s", utc=True),
            freq=pd.Timedelta(seconds=daily.Interval()),
            inclusive="left",
        )
        .strftime("%Y-%m-%d")
        .tolist()
    )

    latitude: float = response.Latitude()
    longitude: float = response.Longitude()

    # Create a DailyWeather object for each day in the API response.
    for i in range(len(date)):
        output.append(
            DailyWeather(
                date=date[i],
                latitude=latitude,
                longitude=longitude,
                wmo_description=wmo_description[i],
                max_temp=max_temp[i],
                min_temp=min_temp[i],
                max_apparent_temp=max_apparent_temp[i],
                min_apparent_temp=min_apparent_temp[i],
                sunrise=sunrise[i],
                sunset=sunset[i],
                precipitation_sum=precipitation_sum[i],
                max_wind_speed=max_wind_speed[i],
            )
        )

    return output


def parse_current_weather_api_response(response: WeatherApiResponse) -> dict[str, Any]:
    """
    Parse the response from the OpenMeteo API and extract the current weather data.

    Args:
        response (WeatherApiResponse): The response from the OpenMeteo API.

    Returns:
        dict[str, Any]: A dictionary containing the current weather data.
            The keys are the names of the variables and the values are tuples
            containing the corresponding values.
    """
    output: dict[str, Any] = {}
    current: VariablesWithTime | None = response.Current()
    if current is None:
        return output

    output["apparent_temp"] = current.Variables(0).Value()
    output["precipitation"] = current.Variables(1).Value()
    output["wmo_description"] = WMO_WEATHER_CODES[int(current.Variables(2).Value())]
    output["is_day"] = current.Variables(3).Value()
    output["wind_gusts"] = current.Variables(4).Value()
    output["visibility"] = current.Variables(5).Value()

    return output


def parse_hourly_weather_api_response(response: WeatherApiResponse) -> dict[str, Any]:
    """
    Parse the response from the OpenMeteo API and extract the hourly weather data.

    Args:
        response (WeatherApiResponse): The response from the OpenMeteo API.

    Returns:
        dict[str, Any]: A dictionary containing the hourly weather data.
            The keys are the names of the variables and the values are tuples
            containing the corresponding values.
    """
    output: dict[str, Any] = {}

    hourly: VariablesWithTime | None = response.Hourly()
    if hourly is None:
        return output

    output["temperature"] = hourly.Variables(0).ValuesAsNumpy()
    output["humidity"] = hourly.Variables(1).ValuesAsNumpy()
    output["apparent_temperature"] = hourly.Variables(2).ValuesAsNumpy()
    output["precipitation"] = hourly.Variables(3).ValuesAsNumpy()
    output["weather_code"] = hourly.Variables(4).ValuesAsNumpy()
    output["wind_speed"] = hourly.Variables(5).ValuesAsNumpy()

    output["date"] = (
        pd.date_range(
            start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
            end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
            freq=pd.Timedelta(seconds=hourly.Interval()),
            inclusive="left",
        )
        .strftime("%Y-%m-%d")
        .tolist()
    )

    return output
