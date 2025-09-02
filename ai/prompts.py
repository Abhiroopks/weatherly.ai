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
