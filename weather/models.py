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


class Weather(BaseModel):
    """
    A class representing weather data.
    """

    def __init__(self, weather: WeatherApiResponse) -> None:
        """
        Initialize the Weather object with data from a WeatherApiResponse.

        :param weather: A WeatherApiResponse object containing weather data.
        """
        current = weather.Current()

        super().__init__(
            lat=weather.Latitude(),
            lon=weather.Longitude(),
            temp=current.Variables(0).Value(),
            precipitation=current.Variables(1).Value(),
            weather_code=current.Variables(2).Value(),
            weather_description=WMO_WEATHER_CODES[current.Variables(2).Value()],
        )

    lat: float
    lon: float
    temp: float
    precipitation: float
    weather_code: int
    weather_description: str
