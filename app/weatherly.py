from fastapi import APIRouter, FastAPI, HTTPException, Path

from geolocate import get_geo_from_address
from models.core import Coordinate
from models.weather import (
    DailyWeatherReport,
    HourlyWeatherReport,
)
from weather.cache import WeatherCache
from weather.weather import (
    get_daily_weather_report,
    get_hourly_weather_report,
)

MAX_DAYS: int = 7
MAX_HOURS: int = 24


class WeatherlyAppWrapper(FastAPI):
    def __init__(self, cache: WeatherCache) -> None:
        """
        Initialize a WeatherlyAppWrapper object.

        Args:
            cache (WeatherCache): A WeatherCache object to use for storing and retrieving weather data.

        Returns:
            None
        """
        super().__init__()
        self.cache: WeatherCache = cache

        router: APIRouter = APIRouter()
        router.add_api_route("/", self.read_root)
        router.add_api_route("/weather/daily/{address}/{days}", self.get_weather_daily)
        router.add_api_route("/weather/today/{address}", self.get_weather_today)
        router.add_api_route(
            "/weather/hourly/{address}/{hours}", self.get_weather_hourly
        )
        router.add_api_route("/weather/current/{address}", self.get_current_weather)
        self.include_router(router)

    def read_root(self) -> dict[str, str]:
        """
        Root endpoint of the API.

        Returns a JSON object with a single key-value pair: {"Hello": "World"}.
        """
        return {"Hello": "World"}

    def get_current_weather(
        self,
        address: str = Path(
            ..., description="Address to generate current weather data for"
        ),
    ) -> HourlyWeatherReport:
        """
        Generates the current weather data for the given address.

        Args:
            address (str): The address to generate the current weather data for.

        Returns:
            HourlyWeatherReport: An object containing the current weather details for the given address.
        """
        geo: dict | None = get_geo_from_address(address)
        if geo is None:
            raise HTTPException(status_code=500, detail="Failed to geocode address")

        lat: float = geo["lat"]
        lon: float = geo["lon"]
        loc: Coordinate = Coordinate(lat, lon)
        return get_hourly_weather_report(
            cache=self.cache,
            city=geo["address"]["city"],
            state=geo["address"]["state"],
            location=loc,
            hours=1,
        )

    def get_weather_daily(
        self,
        days: int = Path(..., description="Number of days"),
        address: str = Path(..., description="Address to generate weather data for"),
    ) -> DailyWeatherReport:
        """
        Generates a daily weather report for the given address for the next {days} days.

        Args:
            days (int): The number of days to generate the weather report for.
            address (str): The address to generate the weather report for.

        Returns:
            DailyWeatherReport: An object containing the weather details for the given address for the next {days} days.
        """
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

    def get_weather_today(
        self, address: str = Path(..., description="Address")
    ) -> DailyWeatherReport:
        """
        Generates a daily weather report for the given address for today.

        Args:
            address: The address to generate the weather report for.

        Returns:
            DailyWeatherReport: An object containing the weather details for the given address for today.
        """
        return self.get_weather_daily(1, address)

    def get_weather_hourly(
        self,
        address: str = Path(..., description="Address to generate weather data for"),
        hours: int = Path(
            ..., description="Number of hours to generate weather data for"
        ),
    ) -> HourlyWeatherReport:
        """
        Generates a weather report for a single location for the next {hours} hours.

        Args:
            address: The address to generate weather data for.
            hours: The number of hours to generate weather data for.

        Returns:
            HourlyWeatherReport: A HourlyWeatherReport object containing the weather details.

        """
        if hours > MAX_HOURS:
            raise HTTPException(
                status_code=400,
                detail=f"Hours must be less than or equal to {MAX_HOURS}",
            )

        geo: dict | None = get_geo_from_address(address)
        if geo is None:
            raise HTTPException(status_code=500, detail="Failed to geocode address")

        lat: float = geo["lat"]
        lon: float = geo["lon"]

        return get_hourly_weather_report(
            location=Coordinate(lat, lon),
            hours=hours,
            city=geo["address"]["city"],
            state=geo["address"]["state"],
            cache=self.cache,
        )
