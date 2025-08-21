import time
from directions.directions import get_directions, split_directions
from directions.models import Coordinates
from weather.models import WeatherReport
from weather.weather import get_weather
from prompts import WEATHER_DESCRIPTION

from openai import OpenAI
from tools import get_key

OPENAI = OpenAI(
    api_key=get_key("openrouter.ai.key"), base_url="https://openrouter.ai/api/v1"
)


def main() -> None:

    start_time = time.time()
    directions: Coordinates = get_directions()
    directions_time = time.time() - start_time
    print(f"get_directions: {directions_time:.2f} seconds")

    start_time = time.time()
    geo_points: dict[str, Coordinates] = split_directions(directions)
    split_time = time.time() - start_time
    print(f"split_directions: {split_time:.2f} seconds")

    start_time = time.time()
    weather_data: list[WeatherReport] = get_weather(geo_points, use_cache=False)
    weather_time = time.time() - start_time
    print(f"get_weather: {weather_time:.2f} seconds")

    content = WEATHER_DESCRIPTION.format(str(weather_data))
    start_time = time.time()
    try:
        response = OPENAI.chat.completions.create(
            model="openai/gpt-oss-20b:free",
            messages=[
                {
                    "role": "user",
                    "content": content,
                }
            ],
        )
    except Exception as e:
        print(e)

    openai_time = time.time() - start_time
    print(f"OpenAI call: {openai_time:.2f} seconds")

    try:
        print(response.choices[0].message.content)
    except Exception as e:
        print(e)


if __name__ == "__main__":
    main()
