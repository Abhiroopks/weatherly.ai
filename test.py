import time

from directions.directions import get_directions, split_directions
from directions.models import Coordinates
from main import get_geo_from_address
from weather.models import WeatherReport
from weather.weather import generate_weather_report, get_weather


def main() -> None:
    start_address: str = "Freehold Raceway Mall, NJ"
    end_address: str = "Princeton University, NJ"

    total_time: float = 0
    time_diff: float = 0

    start_time = time.time()
    start_geo = get_geo_from_address(start_address)
    end_geo = get_geo_from_address(end_address)
    time_diff = time.time() - start_time
    total_time += time_diff
    print(f"Geocoding took {time_diff} seconds")

    start_city = start_geo[0]["components"]["_normalized_city"]
    start_state = start_geo[0]["components"]["state"]
    end_city = end_geo[0]["components"]["_normalized_city"]
    end_state = end_geo[0]["components"]["state"]

    start_coord = Coordinates(
        (start_geo[0]["geometry"]["lat"], start_geo[0]["geometry"]["lng"])
    )
    end_coord = Coordinates(
        (end_geo[0]["geometry"]["lat"], end_geo[0]["geometry"]["lng"])
    )

    start_time = time.time()
    directions = get_directions(start_coord, end_coord)
    time_diff = time.time() - start_time
    total_time += time_diff
    print(f"Getting directions took {time_diff} seconds")

    start_time = time.time()
    geo_points = split_directions(directions)
    time_diff = time.time() - start_time
    total_time += time_diff
    print(f"Splitting directions took {time_diff} seconds")

    start_time = time.time()
    weather_data = get_weather(geo_points, use_cache=False)
    time_diff = time.time() - start_time
    total_time += time_diff
    print(f"Getting weather took {time_diff} seconds")

    start_time = time.time()
    weather_report: WeatherReport = generate_weather_report(
        weather_data, start_city, start_state, end_city, end_state
    )
    time_diff = time.time() - start_time
    total_time += time_diff
    print(f"Generating report took {time_diff} seconds")

    print(weather_report)

    print(f"Total time: {total_time}")


if __name__ == "__main__":
    main()
