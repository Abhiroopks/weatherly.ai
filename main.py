from app.weatherly import WeatherlyAppWrapper
from weather.cache import RedisWeatherCache

REDIS_CACHE: RedisWeatherCache = RedisWeatherCache(host="redis")
app: WeatherlyAppWrapper = WeatherlyAppWrapper(cache=REDIS_CACHE)
