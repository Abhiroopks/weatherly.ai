import json

import redis
from fastapi.encoders import jsonable_encoder
from pydantic_core import from_json

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

    def add_weather_data(self, cache_key: str, weather_data: Weather) -> None:
        json_weather_data = json.dumps(jsonable_encoder(weather_data))
        self.redis_client.hset(cache_key, "weather_data", json_weather_data)
        self.redis_client.expire(cache_key, self.expiration_time)

    def get_weather_data(self, cache_key: str) -> Weather:
        weather_data = self.redis_client.hget(cache_key, "weather_data")
        weather_obj = Weather.model_validate(
            from_json(weather_data, allow_partial=True)
        )
        return weather_obj

    def has_weather_data(self, cache_key: str) -> bool:
        return self.redis_client.exists(cache_key)
