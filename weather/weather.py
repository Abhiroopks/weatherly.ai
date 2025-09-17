from datetime import datetime, timedelta

import openmeteo_requests
import pandas as pd
import requests_cache
from openmeteo_sdk.VariablesWithTime import VariablesWithTime
from openmeteo_sdk.WeatherApiResponse import WeatherApiResponse
from retry_requests import retry

from ai.chat import chat
from ai.prompts import (
    DAILY_WEATHER_DESCRIPTION,
    HOURLY_WEATHER_DESCRIPTION,
)
from models.core import Coordinate
from models.weather import (
    IDEAL_TEMP_RANGE,
    WEATHER_COMFORT_WEIGHTS,
    WMO_WEATHER_CODES,
    DailyWeather,
    DailyWeatherReport,
    HourlyWeather,
    HourlyWeatherReport,
)
from weather.cache import WeatherCache

# Number of days to forecast. Used in openmeteo API call.
FORECAST_DAYS: int = 7

# Number of hours to forecast. Used in openmeteo API call.
FORECAST_HOURS: int = 24

# Date formats.
HOURLY_FMT: str = "%H:00_%d-%m-%Y"
DAILY_FMT: str = "%d-%m-%Y"

# Setup the Open-Meteo API client with cache and retry on error.
CACHE_SESSION = requests_cache.CachedSession(".cache", expire_after=3600)
RETRY_SESSION = retry(CACHE_SESSION, retries=5, backoff_factor=0.2)
OPENMETEO = openmeteo_requests.Client(session=RETRY_SESSION)  # type: ignore
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"


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


def calculate_comfort_score(
    max_precip: float,
    mean_temp: float,
    max_gust: float,
    min_visibility: float,
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

    Returns:
        int: A rounded integer representing the overall comfort score, where a
        higher score indicates more comfortable weather conditions.
    """

    comfort_score = (
        precipitation_score(max_precip) * WEATHER_COMFORT_WEIGHTS["precipitation"]
        + temperature_score(mean_temp) * WEATHER_COMFORT_WEIGHTS["apparent_temperature"]
        + wind_score(max_gust) * WEATHER_COMFORT_WEIGHTS["wind"]
        + visibility_score(min_visibility) * WEATHER_COMFORT_WEIGHTS["visibility"]
    )

    return round(comfort_score)


def generate_llm_hourly_description(
    weather_data: list[HourlyWeather], location: str
) -> str | None:
    content: str = HOURLY_WEATHER_DESCRIPTION.format(location, weather_data)

    return chat(prompt=content)


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


def get_daily_weather_report(
    cache: WeatherCache,
    city: str,
    state: str,
    loc: Coordinate,
    days: int = 1,
) -> DailyWeatherReport:
    prefix: str = "daily"

    weather_days: list[DailyWeather] = []

    # Loop through the given number of days and get the weather for each day.
    for day_offset in range(days):
        date: datetime = datetime.today() + timedelta(days=day_offset)
        date_str: str = date.strftime(DAILY_FMT)
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
                _date: datetime = datetime.now() + timedelta(days=_day_offset)
                _full_prefix: str = f"{prefix}_{_date.strftime(DAILY_FMT)}"
                cache.add_weather(_full_prefix, loc, _daily_weather)

    description: str | None = generate_llm_daily_description(
        weather_days, f"{city}, {state}"
    )

    if description is None:
        description = "Failed to generate via LLM."

    return DailyWeatherReport(data=weather_days, description=description)


def get_hourly_weather_report(
    location: Coordinate,
    hours: int,
    city: str,
    state: str,
    cache: WeatherCache,
) -> HourlyWeatherReport:
    prefix: str = "hourly"
    weather_hours: list[HourlyWeather] = []

    for hour_offset in range(hours):
        date: datetime = datetime.now() + timedelta(hours=hour_offset)
        date_str: str = date.strftime(HOURLY_FMT)
        full_prefix: str = f"{prefix}_{date_str}"
        # Check if the weather for this day is already in the cache.
        if cache.has_weather(full_prefix, location):
            hourly_weather: HourlyWeather = cache.get_weather(full_prefix, location)  # type: ignore
            weather_hours.append(hourly_weather)
        else:
            # If we don't have cached data, fetch it from the API and cache it.
            params: dict = {
                "latitude": location.lat,
                "longitude": location.lon,
                "hourly": [
                    "apparent_temperature",
                    "precipitation",
                    "weather_code",
                    "wind_speed_10m",
                    "relative_humidity_2m",
                    "temperature_2m",
                ],
                "forecast_hours": FORECAST_HOURS,
            }

            response: list[WeatherApiResponse] = OPENMETEO.weather_api(
                WEATHER_URL, params=params
            )

            # Parse the API response into a list of HourlyWeather objects.
            hourly_weather_list: list[HourlyWeather] = (
                parse_hourly_weather_api_response(response[0])
            )

            # Find the HourlyWeather object for the current hour and add it to the list.
            for _hourly_weather in hourly_weather_list:
                if _hourly_weather.date == date_str:
                    weather_hours.append(_hourly_weather)

            # Cache the weather for each hour.
            for _hour_offset in range(FORECAST_HOURS):
                _hourly_weather: HourlyWeather = hourly_weather_list[_hour_offset]
                _hour: datetime = datetime.now() + timedelta(hours=_hour_offset)
                _full_prefix: str = f"{prefix}_{_hour.strftime(HOURLY_FMT)}"
                cache.add_weather(_full_prefix, location, _hourly_weather)

    description: str | None = generate_llm_hourly_description(
        weather_hours, f"{city}, {state}"
    )

    if description is None:
        description = "Failed to generate via LLM."

    return HourlyWeatherReport(data=weather_hours, description=description)


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
        datetime.fromtimestamp(ts).strftime("%I:%M %p")
        for ts in daily.Variables(5).ValuesInt64AsNumpy()
    ]
    sunset: list[str] = [
        datetime.fromtimestamp(ts).strftime("%I:%M %p")
        for ts in daily.Variables(6).ValuesInt64AsNumpy()
    ]

    # Extract the precipitation sum and maximum wind speed.
    precipitation_sum: list[float] = daily.Variables(7).ValuesAsNumpy().tolist()
    max_wind_speed: list[float] = daily.Variables(8).ValuesAsNumpy().tolist()

    # Extract the date from the API response.
    date = (
        pd.date_range(
            start=pd.to_datetime(daily.Time(), unit="s", utc=True),
            end=pd.to_datetime(daily.TimeEnd(), unit="s", utc=True),
            freq=pd.Timedelta(seconds=daily.Interval()),
            inclusive="left",
        )
        .strftime(DAILY_FMT)
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
                max_temp_c=max_temp[i],
                min_temp_c=min_temp[i],
                max_apparent_temp_c=max_apparent_temp[i],
                min_apparent_temp_c=min_apparent_temp[i],
                sunrise=sunrise[i],
                sunset=sunset[i],
                precipitation_sum_mm=precipitation_sum[i],
                max_wind_speed_kmh=max_wind_speed[i],
            )
        )

    return output


def parse_hourly_weather_api_response(
    response: WeatherApiResponse,
) -> list[HourlyWeather]:
    output: list[HourlyWeather] = []

    hourly: VariablesWithTime | None = response.Hourly()
    if hourly is None:
        return output

    apparent_temp: list[float] = hourly.Variables(0).ValuesAsNumpy().tolist()
    precipitation: list[float] = hourly.Variables(1).ValuesAsNumpy().tolist()
    weather_code: list[str] = [
        WMO_WEATHER_CODES[int(code)]
        for code in hourly.Variables(2).ValuesAsNumpy().tolist()
    ]
    wind_speed_10m: list[float] = hourly.Variables(3).ValuesAsNumpy().tolist()
    relative_humidity_2m: list[float] = hourly.Variables(4).ValuesAsNumpy().tolist()
    temp: list[float] = hourly.Variables(5).ValuesAsNumpy().tolist()

    date = (
        pd.date_range(
            start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
            end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
            freq=pd.Timedelta(seconds=hourly.Interval()),
            inclusive="left",
        )
        .strftime(HOURLY_FMT)
        .tolist()
    )

    latitude: float = response.Latitude()
    longitude: float = response.Longitude()

    for i in range(len(date)):
        output.append(
            HourlyWeather(
                date=date[i],
                latitude=latitude,
                longitude=longitude,
                apparent_temp_c=apparent_temp[i],
                temp_c=temp[i],
                precipitation_sum_mm=precipitation[i],
                wmo_description=weather_code[i],
                wind_speed_kmh=wind_speed_10m[i],
                relative_humidity_pct=relative_humidity_2m[i],
            )
        )

    return output
