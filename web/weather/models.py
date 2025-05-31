from annotated_types import T
from openmeteo_sdk.WeatherApiResponse import WeatherApiResponse
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
IDEAL_TEMP_RANGE = (20, 25)


class Weather(BaseModel):
    """
    A class representing weather data.
    """

    def __init__(self, weather: WeatherApiResponse = None, **kwargs: dict) -> None:

        if weather is None:
            super().__init__(**kwargs)
            return

        current = weather.Current()

        super().__init__(
            lat=weather.Latitude(),
            lon=weather.Longitude(),
            apparent_temp=current.Variables(0).Value(),
            precipitation=current.Variables(1).Value(),
            weather_description=WMO_WEATHER_CODES[current.Variables(2).Value()],
            is_day=current.Variables(3).Value(),
            wind_gusts=current.Variables(4).Value(),
            visibility=current.Variables(5).Value(),
        )

    lat: float
    lon: float
    apparent_temp: float
    precipitation: float
    weather_description: str
    is_day: bool
    wind_gusts: float
    visibility: float


class WeatherReport(BaseModel):

    max_precip: float
    mean_temp: float
    max_gust: float
    min_visibility: float
    is_day: bool
    comfort_score: int
    description: str
    weather_points: list[Weather]
