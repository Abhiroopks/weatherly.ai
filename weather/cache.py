import json

import geohash
import redis
from fastapi.encoders import jsonable_encoder
from pydantic_core import from_json

from directions.models import Coordinates
from weather.models import CurrentWeather, DailyWeather

# Expires after 6 hours
DAILY_WEATHER_EXPIRATION_TIME: int = 21600

# Expires after 1 hour
CURRENT_WEATHER_EXPIRATION_TIME: int = 3600

# Expires after 1 hour
HOURLY_WEATHER_EXPIRATION_TIME: int = 3600


class WeatherDataCache:
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
        self, prefix: str, loc: Coordinates, weather_data: CurrentWeather | DailyWeather
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

    def has_weather(self, prefix: str, loc: Coordinates) -> bool:
        """Check if the weather data exists in the cache."""
        full_cache_key: str = prefix + "_" + generate_cache_key(loc)
        return self.redis_client.exists(full_cache_key) == 1

    def get_weather(
        self, prefix: str, loc: Coordinates
    ) -> CurrentWeather | DailyWeather | None:
        """Get the weather data from the cache."""
        full_cache_key: str = prefix + "_" + generate_cache_key(loc)
        cached_data: str | None = self.redis_client.hget(full_cache_key, "weather_data")
        if cached_data is None:
            return None
        return (
            CurrentWeather.model_validate_json(cached_data)
            if prefix == "current"
            else DailyWeather.model_validate_json(cached_data)
        )


def generate_cache_key(loc: Coordinates) -> str:
    """
    Generate a cache key using geohash encoding from a Coordinates object.
    This function encodes the given geographical coordinates into a geohash
    string with a precision of 4, which corresponds to about 39km x 20km block.
    Args:
        loc (Coordinates): The location for which to generate a cache key.
    Returns:
        str: A geohash string used as the cache key.
    """
    geohash_key = geohash.encode(loc.lat, loc.lon, precision=4)
    return geohash_key
