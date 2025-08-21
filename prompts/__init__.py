"""
A place to store prompts for LLM tools.
"""

WEATHER_DESCRIPTION: str = """
Generate a human readable text description of the weather along a driving route. 
There should only be a few sentences to summarize the weather and 
it should be easily understood by the average user. Starting location is {}, {} 
and ending location is {}, {}. Locations are given as city,state. Overall 
comfort score is {}. Units for temperature are celsius, wind speed is in
kilometers per hour, visibility in meters, and precipitation in mm. 
The weather data is: {}
"""
