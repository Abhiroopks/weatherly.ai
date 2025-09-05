import datetime
from typing import Literal

from pydantic import BaseModel

CURRENT_WEATHER_PARAMS: list[str] = [
    "apparent_temp",
    "precipitation",
    "weather_description",
    "is_day",
    "wind_gusts",
    "visibility",
]

HOURLY_WEATHER_PARAMS: list[str] = [
    "temperature",
    "humidity",
    "apparent_temperature",
    "precipitation",
    "weather_code",
    "wind_speed",
]

DAILY_WEATHER_PARAMS: list[str] = [
    "weather_code",
    "max_temp",
    "min_temp",
    "apparent_temp_max",
    "apparent_temp_min",
    "sunrise",
    "sunset",
    "precipitation_sum",
    "wind_speed_max",
]

# Mapping of WMO weather codes to weather descriptions.
WMO_WEATHER_CODES: dict[int, str] = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Drizzle: Light",
    53: "Drizzle: Moderate",
    55: "Drizzle: Dense",
    56: "Freezing drizzle: Light",
    57: "Freezing drizzle: Dense",
    61: "Rain: Slight",
    63: "Rain: Moderate",
    65: "Rain: Heavy",
    66: "Freezing rain: Light",
    67: "Freezing rain: Heavy",
    71: "Snowfall: Slight",
    73: "Snowfall: Moderate",
    75: "Snowfall: Heavy",
    77: "Snow grains",
    80: "Rain showers: Slight",
    81: "Rain showers: Moderate",
    82: "Rain showers: Violent",
    85: "Snow showers: Slight",
    86: "Snow showers: Heavy",
    95: "Thunderstorm: Slight or moderate",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}

# Weights for calculating the comfort score.
WEATHER_COMFORT_WEIGHTS: dict[str, float] = {
    "precipitation": 0.25,
    "apparent_temperature": 0.2,
    "wind": 0.1,
    "visibility": 0.3,
    "day_night": 0.15,
}

# Ideal temperature in celsius (this is rather subjective).
IDEAL_TEMP_RANGE: tuple[Literal[20], Literal[25]] = (20, 25)


class CurrentWeather(BaseModel):
    """
    A class representing current weather data for a single location.
    """

    apparent_temp: float
    precipitation: float
    weather_description: str
    is_day: bool
    wind_gusts: float
    visibility: float

    def __init__(self, **kwargs: dict) -> None:
        super().__init__(**kwargs)


class DrivingReport(BaseModel):
    max_precip: float
    mean_temp: float
    max_gust: float
    min_visibility: float
    is_day: bool
    comfort_score: int
    description: str


class DailyWeather(BaseModel):
    """
    Weather data for a number of consecutive days, for a single location.
    """

    date: str
    location: str
    max_temp: float
    min_temp: float
    apparent_temp_max: float
    apparent_temp_min: float
    sunrise: datetime.time
    sunset: datetime.time
    precipitation_sum: float
    wind_speed_max: float

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, **kwargs: dict) -> None:
        super().__init__(**kwargs)


class HourlyWeather(BaseModel):
    """
    Weather data for a number of consecutive hours, for a single location.
    """

    date: str
    location: str
    temp: float
    apparent_temp: float
    humidity: float
    precipitation_sum: float
    wind_speed: float

    class Config:
        arbitrary_types_allowed = True
