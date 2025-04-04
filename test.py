import json

from directions.directions import get_directions, split_directions
from directions.models import Coordinates, Directions
from weather.models import Weather
from weather.weather import get_weather


def read_directions(fname: str) -> Directions:
    """
    Reads a JSON file and returns a Directions object.

    :param fname: The path to the JSON file to read.
    :return: A Directions object.
    """
    with open(fname, "r") as f:
        return Directions(json.load(f))


def main() -> None:
    directions = get_directions()
    # directions: Directions = read_directions("directions.json")
    geo_points: list[Coordinates] = split_directions(directions, interval=2000)

    weather_data: list[Weather] = get_weather(geo_points)
    for weather in weather_data:
        print(weather)


if __name__ == "__main__":
    main()
