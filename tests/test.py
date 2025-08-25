import json
from typing import Tuple

from directions.directions import get_directions, split_directions
from directions.models import Coordinates, Directions
from main import get_geo_from_address
from weather.models import Weather, WeatherReport
from weather.weather import (
    calculate_comfort_score,
    generate_llm_description,
    generate_weather_description_manually,
    generate_weather_report,
    get_weather,
)


def load_json(file_path: str) -> dict | list:
    with open(file_path, "r") as f:
        return json.load(f)


class TestApp:
    def test_geocode(self):
        """
        Tests that the geocode function returns a non-empty list of geo dictionaries when
        given a valid address.
        """

        geos: list[dict] = get_geo_from_address("Princeton University, Princeton, NJ")

        assert len(geos) > 0

    def test_directions(self):
        """
        Tests that the get_directions function returns a non-None Directions object
        when given valid start and end coordinates.
        """
        start_geo: dict = load_json("start_geo.json")
        end_geo: dict = load_json("end_geo.json")

        directions: Directions = get_directions(
            Coordinates(
                (
                    start_geo["geometry"]["lat"],
                    start_geo["geometry"]["lng"],
                )
            ),
            Coordinates((end_geo["geometry"]["lat"], end_geo["geometry"]["lng"])),
        )

        assert directions is not None

    def test_weather(self):
        """
        Tests that the get_weather function returns a non-None list of Weather objects
        when given valid directions.
        """

        directions_json: dict = load_json("directions.json")
        directions: Directions = Directions(directions_json)

        geo_points: list[Tuple[str, Coordinates]] = split_directions(directions)
        weather_data: list[Weather] = get_weather(geo_points, use_cache=False)

        assert weather_data is not None

    def test_weather_description_llm(self):
        """
        Tests that the generate_llm_description function returns a non-None string when
        given valid weather data and start/end addresses.
        """

        weather_data_json: list[dict] = load_json("weather_data.json")
        weather_data: list[Weather] = [Weather(**w) for w in weather_data_json]

        start_geo: dict = load_json("start_geo.json")
        end_geo: dict = load_json("end_geo.json")

        max_precip: float = max([weather.precipitation for weather in weather_data])

        # Calculate the average temperature over the data points.
        mean_temp: float = sum(
            [weather.apparent_temp for weather in weather_data]
        ) / len(weather_data)

        # Highest wind gust over the route.
        max_gust: float = max([weather.wind_gusts for weather in weather_data])

        # Lowest visibility over the route
        min_visibility: float = min([weather.visibility for weather in weather_data])

        # If any portion of the route is not day, then the route is night.
        is_day: bool = all([weather.is_day for weather in weather_data])

        comfort_score: int = calculate_comfort_score(
            max_precip, mean_temp, max_gust, min_visibility, is_day
        )

        weather_description: str = generate_llm_description(
            weather_data=weather_data,
            comfort_score=comfort_score,
            start_city=start_geo["components"]["_normalized_city"],
            start_state=start_geo["components"]["state"],
            end_city=end_geo["components"]["_normalized_city"],
            end_state=end_geo["components"]["state"],
        )

        assert weather_description is not None

    def test_weather_description_manual(self):
        """
        Tests that the generate_weather_description_manually function returns a non-None
        string when given valid weather data and start/end addresses.
        """
        weather_data_json: list[dict] = load_json("weather_data.json")
        weather_data: list[Weather] = [Weather(**w) for w in weather_data_json]

        start_geo: dict = load_json("start_geo.json")
        end_geo: dict = load_json("end_geo.json")

        max_precip: float = max([weather.precipitation for weather in weather_data])

        # Calculate the average temperature over the data points.
        mean_temp: float = sum(
            [weather.apparent_temp for weather in weather_data]
        ) / len(weather_data)

        # Highest wind gust over the route.
        max_gust: float = max([weather.wind_gusts for weather in weather_data])

        # Lowest visibility over the route
        min_visibility: float = min([weather.visibility for weather in weather_data])

        # If any portion of the route is not day, then the route is night.
        is_day: bool = all([weather.is_day for weather in weather_data])

        comfort_score: int = calculate_comfort_score(
            max_precip, mean_temp, max_gust, min_visibility, is_day
        )

        weather_description: str = generate_weather_description_manually(
            weather_data=weather_data,
            comfort_score=comfort_score,
            start_city=start_geo["components"]["_normalized_city"],
            start_state=start_geo["components"]["state"],
            end_city=end_geo["components"]["_normalized_city"],
            end_state=end_geo["components"]["state"],
        )

        assert weather_description is not None

    def test_weather_report(self):
        """
        Tests that the generate_weather_report function returns a non-None WeatherReport
        object when given valid weather data and start/end addresses.
        """
        weather_data_json: list[dict] = load_json("weather_data.json")
        weather_data: list[Weather] = [Weather(**w) for w in weather_data_json]

        start_geo: dict = load_json("start_geo.json")
        end_geo: dict = load_json("end_geo.json")

        weather_report: WeatherReport = generate_weather_report(
            weather_data=weather_data,
            start_city=start_geo["components"]["_normalized_city"],
            start_state=start_geo["components"]["state"],
            end_city=end_geo["components"]["_normalized_city"],
            end_state=end_geo["components"]["state"],
        )

        assert weather_report is not None
