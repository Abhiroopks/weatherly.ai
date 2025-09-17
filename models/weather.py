from typing import Literal

from pydantic import BaseModel

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


class DailyWeather(BaseModel):
    """
    Weather data for a single day, for a single location.
    """

    date: str
    latitude: float
    longitude: float
    wmo_description: str
    max_temp_c: float
    min_temp_c: float
    max_apparent_temp_c: float
    min_apparent_temp_c: float
    sunrise: str
    sunset: str
    precipitation_sum_mm: float
    max_wind_speed_kmh: float


class DailyWeatherReport(BaseModel):
    data: list[DailyWeather]
    description: str


class HourlyWeather(BaseModel):
    """
    Weather data for a number of consecutive hours, for a single location.
    """

    date: str
    latitude: float
    longitude: float
    temp_c: float
    apparent_temp_c: float
    relative_humidity_pct: float
    precipitation_sum_mm: float
    wind_speed_kmh: float
    wmo_description: str


class HourlyWeatherReport(BaseModel):
    data: list[HourlyWeather]
    description: str
