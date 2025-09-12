import json
from abc import ABC, abstractmethod

import geohash
import redis
from fastapi.encoders import jsonable_encoder

from models.core import Coordinate
from models.weather import CurrentWeather, DailyWeather

# Expires after 6 hours
DAILY_WEATHER_EXPIRATION_TIME: int = 21600

# Expires after 1 hour
CURRENT_WEATHER_EXPIRATION_TIME: int = 3600

# Expires after 1 hour
HOURLY_WEATHER_EXPIRATION_TIME: int = 3600


class WeatherCache(ABC):
    """An abstract class for both cache classes."""

    @abstractmethod
    def add_weather(
        self, prefix: str, loc: Coordinate, weather_data: CurrentWeather | DailyWeather
    ) -> None:
        """Add weather data to the cache. Abstract method."""
        pass

    @abstractmethod
    def get_weather(
        self, prefix: str, loc: Coordinate
    ) -> CurrentWeather | DailyWeather | None:
        """Get weather data from the cache. Abstract method."""
        pass

    @abstractmethod
    def has_weather(self, prefix: str, loc: Coordinate) -> bool:
        """Check if the cache has the weather data. Abstract method."""
        pass


class RedisWeatherCache(WeatherCache):
    def __init__(
        self,
        redis_host: str = "localhost",
        redis_port: int = 6379,
    ):  # 1 hour expiration time
        """
        Initialize the WeatherDataCache object with a Redis client and cache expiration time.

        Args:
            redis_host (str): The hostname of the Redis server. Defaults to 'localhost'.
            redis_port (int): The port number of the Redis server. Defaults to 6379.
        """
        self.redis_client = redis.Redis(host=redis_host, port=redis_port)

    def add_weather(
        self, prefix: str, loc: Coordinate, weather_data: CurrentWeather | DailyWeather
    ) -> None:
        full_cache_key: str = prefix + "_" + generate_cache_key(loc)
        json_weather_data = json.dumps(jsonable_encoder(weather_data))
        self.redis_client.hset(full_cache_key, "weather_data", json_weather_data)
        expiration_time: int = (
            CURRENT_WEATHER_EXPIRATION_TIME
            if prefix == "current"
            else DAILY_WEATHER_EXPIRATION_TIME
        )
        self.redis_client.expire(full_cache_key, expiration_time)

    def has_weather(self, prefix: str, loc: Coordinate) -> bool:
        """Check if the weather data exists in the cache."""
        full_cache_key: str = prefix + "_" + generate_cache_key(loc)
        return self.redis_client.exists(full_cache_key) == 1

    def get_weather(
        self, prefix: str, loc: Coordinate
    ) -> CurrentWeather | DailyWeather | None:
        """Get the weather data from the cache."""
        full_cache_key: str = prefix + "_" + generate_cache_key(loc)
        cached_data: str | None = self.redis_client.hget(full_cache_key, "weather_data")  # type: ignore
        if cached_data is None:
            return None
        return (
            CurrentWeather.model_validate_json(cached_data)
            if prefix == "current"
            else DailyWeather.model_validate_json(cached_data)
        )


class TestDataCache(WeatherCache):
    """A test version of the WeatherDataCache that doesn't require a Redis server"""

    def __init__(self) -> None:
        self.cache: dict[str, str] = {}

    def add_weather(self, prefix: str, loc: Coordinate, weather_data) -> None:
        full_cache_key: str = prefix + "_" + generate_cache_key(loc)
        self.cache[full_cache_key] = json.dumps(jsonable_encoder(weather_data))

    def has_weather(self, prefix: str, loc: Coordinate) -> bool:
        full_cache_key: str = prefix + "_" + generate_cache_key(loc)
        return full_cache_key in self.cache

    def get_weather(
        self, prefix: str, loc: Coordinate
    ) -> CurrentWeather | DailyWeather | None:
        full_cache_key: str = prefix + "_" + generate_cache_key(loc)
        cached_data: str | None = self.cache.get(full_cache_key)
        if cached_data is None:
            return None
        return (
            CurrentWeather.model_validate_json(cached_data)
            if prefix == "current"
            else DailyWeather.model_validate_json(cached_data)
        )


def generate_cache_key(loc: Coordinate) -> str:
    """
    Generate a cache key using geohash encoding from a Coordinate object.
    This function encodes the given geographical coordinates into a geohash
    string with a precision of 4, which corresponds to about 39km x 20km block.
    Args:
        loc (Coordinate): The location for which to generate a cache key.
    Returns:
        str: A geohash string used as the cache key.
    """
    geohash_key = geohash.encode(loc.lat, loc.lon, precision=4)
    return geohash_key
