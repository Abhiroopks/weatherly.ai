from openmeteo_sdk.WeatherApiResponse import WeatherApiResponse

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

class Weather:
    def __init__(self, weather: WeatherApiResponse) -> None:
        """
        Initialize the Weather object with data from a WeatherApiResponse.

        :param weather: A WeatherApiResponse object containing weather data.
        """
        self.lat: float = weather.Latitude()
        self.lon: float = weather.Longitude()

        current = weather.Current()
        self.temp: float = current.Variables(0).Value()
        self.precipitation: float = current.Variables(1).Value()
        self.weather_code: int = current.Variables(2).Value()
        self.weather_description: str = WMO_WEATHER_CODES[self.weather_code]

    def __str__(self) -> str:
        """
        Return a string representation of the Weather object.

        :return: A string describing the weather conditions.
        """
        return """
        Coordinates: ({}, {})\n
        Temperature: {}\n
        Precipitation: {}\n
        Weather Description: {}\n
        """.format(
            self.lat, self.lon, self.temp, self.precipitation, self.weather_description
        )

