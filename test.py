from time import time

from directions.directions import get_directions, split_directions
from directions.models import Coordinates
from weather.models import WeatherReport
from weather.weather import generate_weather_report, get_weather


def main() -> None:
    start_time = time()
    directions: Coordinates = get_directions()
    end_time = time()
    print(f"Time to get directions: {end_time - start_time} seconds")

    start_time = time()
    geo_points: dict[str, Coordinates] = split_directions(directions)
    end_time = time()
    print(f"Time to split directions: {end_time - start_time} seconds")

    start_time = time()
    weather_data: list[WeatherReport] = get_weather(geo_points)
    end_time = time()
    print(f"Time to get weather: {end_time - start_time} seconds")

    start_time = time()
    weather_report: WeatherReport = generate_weather_report(weather_data)
    end_time = time()
    print(f"Time to generate weather report: {end_time - start_time} seconds")


if __name__ == "__main__":
    main()
