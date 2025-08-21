from weather.models import WeatherReport
from main import _get_weather_report


def main() -> None:
    start_address: str = "Freehold Raceway Mall, NJ"
    end_address: str = "Princeton University, NJ"

    report: WeatherReport = _get_weather_report(
        start_address, end_address, use_cache=False
    )
    print(report)


if __name__ == "__main__":
    main()
