import json

import redis
from fastapi.encoders import jsonable_encoder
from numpy import full
from pydantic_core import from_json

from weather.models import CurrentWeather


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

    def add_current_weather(self, cache_key: str, weather_data: CurrentWeather) -> None:
        """
        Adds current weather data to the cache under the given cache key.

        Args:
            cache_key (str): The cache key to store the weather data under.
            weather_data (CurrentWeather): The current weather data to store.

        Returns:
            None
        """
        full_cache_key: str = "current_" + cache_key
        json_weather_data = json.dumps(jsonable_encoder(weather_data))
        self.redis_client.hset(full_cache_key, "weather_data", json_weather_data)
        self.redis_client.expire(full_cache_key, self.expiration_time)

    def get_current_weather(self, cache_key: str) -> CurrentWeather:
        """
        Retrieves current weather data from the cache under the given cache key.

        Args:
            cache_key (str): The cache key to retrieve the weather data from.

        Returns:
            CurrentWeather: The current weather data for the given cache key.

        Raises:
            KeyError: If the cache key does not exist in the cache.
        """

        full_cache_key: str = "current_" + cache_key
        weather_data = self.redis_client.hget(full_cache_key, "weather_data")
        weather_obj: CurrentWeather = CurrentWeather.model_validate(
            from_json(weather_data, allow_partial=True)
        )
        return weather_obj

    def has_current_weather(self, cache_key: str) -> bool:
        """
        Checks if current weather data exists in the cache under the given cache key.

        Args:
            cache_key (str): The cache key to check for current weather data.

        Returns:
            bool: True if the current weather data exists in the cache, False otherwise.
        """
        full_cache_key: str = "current_" + cache_key
        return self.redis_client.exists(full_cache_key) == 1
