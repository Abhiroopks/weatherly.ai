from fastapi import APIRouter, FastAPI, HTTPException

from directions.directions import get_directions, split_directions
from geolocate import get_geo_from_address
from models.core import Coordinate
from models.directions import Directions
from models.weather import (
    CurrentWeather,
    DailyWeather,
    DrivingReport,
)
from weather.cache import WeatherCache
from weather.weather import (
    generate_weather_report,
    get_current_weather,
    get_daily_weather_report,
)

MAX_DAYS: int = 7


class WeatherlyAppWrapper(FastAPI):
    def __init__(self, cache: WeatherCache) -> None:
        super().__init__()
        self.cache: WeatherCache = cache

        router: APIRouter = APIRouter()
        router.add_api_route("/", self.read_root)
        router.add_api_route(
            "/weather/drive/{start_address}/{end_address}", self.get_driving_report
        )
        router.add_api_route("/weather/daily/{address}/{days}", self.get_weather_daily)
        router.add_api_route("/weather/today/{address}", self.get_weather_today)
        self.include_router(router)

    def read_root(self) -> dict[str, str]:
        """
        Root endpoint of the API.

        Returns a JSON object with a single key-value pair: {"Hello": "World"}.
        """
        return {"Hello": "World"}

    def _get_driving_report(
        self, start_address: str, end_address: str
    ) -> DrivingReport:
        """
        Generates a weather report for the given start and end addresses.

        Args:
            start_address: The starting address for the route.
            end_address: The ending address for the route.

        Returns:
            DrivingReport: An object containing the weather details for the route.
        """
        start: dict | None = get_geo_from_address(start_address)
        if start is None:
            raise HTTPException(
                status_code=500, detail="Failed to geocode start address"
            )

        end: dict | None = get_geo_from_address(end_address)
        if end is None:
            raise HTTPException(status_code=500, detail="Failed to geocode end address")

        start_coord = Coordinate(lat=start["lat"], lon=start["lon"])
        end_coord = Coordinate(lat=end["lat"], lon=end["lon"])

        try:
            directions: Directions = get_directions(start_coord, end_coord)
            geo_points: list = split_directions(directions)
            weather_data: list[CurrentWeather] = get_current_weather(
                geo_points, self.cache
            )
            weather_report: DrivingReport = generate_weather_report(
                weather_data, start, end
            )
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to generate Driving Report: {e}"
            )

        return weather_report

    def get_driving_report(self, start_address: str, end_address: str) -> DrivingReport:
        """
        Generates a weather report based on the given start and end addresses.

        Args:
            start_address: The starting address for the route.
            end_address: The ending address for the route.

        Returns:
            DrivingReport: An object containing the weather details for the route.
        """
        return self._get_driving_report(start_address, end_address)

    def get_weather_daily(
        self, days: int, address: str
    ) -> dict[str, list[DailyWeather] | str]:
        if days > MAX_DAYS:
            raise HTTPException(
                status_code=400, detail=f"Days must be less than or equal to {MAX_DAYS}"
            )

        geo: dict | None = get_geo_from_address(address)
        if geo is None:
            raise HTTPException(status_code=500, detail="Failed to geocode address")

        lat: float = geo["lat"]
        lon: float = geo["lon"]
        return get_daily_weather_report(
            cache=self.cache,
            city=geo["address"]["city"],
            state=geo["address"]["state"],
            loc=Coordinate(lat, lon),
            days=days,
        )

    def get_weather_today(self, address: str) -> dict[str, list[DailyWeather] | str]:
        return self.get_weather_daily(1, address)

    # @app.get("/weather/hourly/{address}/{hours}")
    # def get_weather_hourly(address: str) -> HourlyWeatherReport:
    #     """
    #     Generates a weather report for a single location for the next {hours} hours.

    #     Args:
    #         address: The address to generate weather data for.
    #         hours: The number of hours to generate weather data for.

    #     Returns:
    #         HourlyWeatherReport: A HourlyWeatherReport object containing the weather details.

    #     """
    #     pass
