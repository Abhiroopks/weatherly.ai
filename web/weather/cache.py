import json

import geohash
import redis
from fastapi.encoders import jsonable_encoder
from pydantic_core import from_json

from directions.models import Coordinates
from weather.models import Weather


class WeatherDataCache:
    def __init__(
        self,
        redis_host: str = "localhost",
        redis_port: int = 6379,
        expiration_time: int = 3600,
    ):  # 1 hour expiration time
        """
        Initialize the WeatherDataCache object with a Redis client and cache expiration time.

        Args:
            redis_host (str): The hostname of the Redis server. Defaults to 'localhost'.
            redis_port (int): The port number of the Redis server. Defaults to 6379.
            expiration_time (int): The expiration time for cached data in seconds. Defaults to 3600 seconds (1 hour).
        """
        self.redis_client = redis.Redis(host=redis_host, port=redis_port)
        self.expiration_time = expiration_time

    def _generate_cache_key(self, loc: Coordinates) -> str:
        """
        Generate a cache key using geohash encoding from a Coordinates object.

        This function encodes the given geographical coordinates into a geohash
        string with a precision of 5, which is then truncated to 5 characters to
        represent approximately 5 miles of precision.

        Args:
            loc (Coordinates): The location for which to generate a cache key.

        Returns:
            str: A truncated geohash string used as the cache key.
        """
        geohash_key = geohash.encode(loc.lat, loc.lon, precision=5)
        return geohash_key[:5]  # truncate to 5 miles precision

    def add_weather_data(self, loc: Coordinates, weather_data: Weather) -> None:
        """
        Add weather data to the cache.

        Args:
            loc (Coordinates): The location for which the weather data is valid.
            weather_data (Weather): The weather data to be added to the cache.

        Returns:
            None
        """
        cache_key = self._generate_cache_key(loc)
        json_weather_data = json.dumps(jsonable_encoder(weather_data))
        self.redis_client.hset(cache_key, "weather_data", json_weather_data)
        self.redis_client.expire(cache_key, self.expiration_time)

    def get_weather_data(self, loc: Coordinates) -> Weather:
        """
        Retrieve weather data from the cache.
        Args:
            loc (Coordinates): The location for which the weather data is requested.

        Returns:
            Weather or None: The weather data associated with the given location.
        """
        cache_key = self._generate_cache_key(loc)
        weather_data = self.redis_client.hget(cache_key, "weather_data")
        weather_obj = Weather.model_validate(from_json(weather_data, allow_partial=True))
        return weather_obj

    def has_weather_data(self, loc: Coordinates) -> bool:
        """
        Check if the cache contains weather data for a given location.

        Args:
            loc (Coordinates): The location for which to check if weather data is cached.

        Returns:
            bool: True if weather data for the given location is found in the cache, False otherwise.
        """
        cache_key = self._generate_cache_key(loc)
        return self.redis_client.exists(cache_key)
