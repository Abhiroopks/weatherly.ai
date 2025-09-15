"""
A place to store prompts for LLM tools.
"""

WEATHER_DESCRIPTION: str = """
Generate a human readable text description of the weather along a driving route. 
There shouldn't be special characters and no new lines.
Write temperatures as 18C (no degree symbol, no special spacing).
There should be a few sentences to summarize the weather and 
it should be easily understood by the average user.
Maximum of 100 words.
Starting location is {}, {} 
and ending location is {}, {}. Locations are given as city,state. Overall 
comfort score is {}. Units for temperature are celsius, wind speed is in
kilometers per hour, visibility in meters, and precipitation in mm. 
The weather data over the course of the route is: {}.
"""

DAILY_WEATHER_DESCRIPTION: str = """
You are given a sequence of daily weather records for a single location. 
Each record has the following fields:

- date: YYYY-MM-DD
- latitude, longitude: coordinates (ignore this field)
- wmo_description: short standardized weather label
- description: empty (ignore this field)
- max_temp, min_temp: daily max and min temperature
- max_apparent_temp, min_apparent_temp: feels-like temperature range
- sunrise, sunset: local times
- precipitation_sum: total daily precipitation
- max_wind_speed: maximum wind speed

TASK:
Produce a human-readable narrative that summarizes the weather over the sequence. 
Keep it concise and clear for a general audience. 
Mention trends in temperature, precipitation, and wind. 
Highlight notable events (storms, heavy rain, unusual heat/cold). 
Do not repeat raw numbers unless they are important for context. 
Do not output JSON or structured data—only a natural language summary.

LOCATION:
{}

WEATHER DATA:
{}
"""

HOURLY_WEATHER_DESCRIPTION: str = """
You are given a sequence of hourly weather records for a single location. 
Each record has the following fields:

- date: HH AM/PM DD-MM-YYYY 
- latitude, longitude: coordinates (ignore this field)
- wmo_description: short standardized weather label
- temp: hourly temperature
- apparent_temp: feels-like temperature
- relative_humidity: percent
- precipitation_sum: hourly precipitation
- wind_speed: wind speed

TASK:
Produce a human-readable narrative that summarizes the weather over the sequence. 
Keep it concise and clear for a general audience. 
Mention trends in temperature, precipitation, and wind. 
Highlight notable events (storms, heavy rain, unusual heat/cold). 
Do not repeat raw numbers unless they are important for context. 
Do not output JSON or structured data—only a natural language summary.

LOCATION:
{}

WEATHER DATA:
{}
"""
