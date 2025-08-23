from typing import Tuple

import openrouteservice
from fastapi import HTTPException
from geopy.distance import geodesic

from directions.models import Coordinates, Directions, generate_cache_key
from tools import get_key

"""
This module provides functionality to interact with the OpenRouteService API
for obtaining driving directions between two geographical coordinates. It includes
functions to read an API key, fetch directions from the API, save directions to a
JSON file, and manage stored directions. The module is designed to facilitate 
route planning and navigation tasks by leveraging external routing services.
"""


def split_directions(
    directions: Directions, interval: int = 48000, include_end: bool = True
) -> list[Tuple[str, Coordinates]]:
    """
    Splits a given route into multiple geographical points at specified intervals.

    This function takes a Directions object and splits the route into multiple
    Coordinates objects based on the specified distance interval. It interpolates
    additional points between the original coordinates if the distance between them
    exceeds the specified interval. The function also allows the option to include
    the end point in the result.

    Args:
        directions (Directions): The Directions object containing the route's geographical coordinates.
        interval (int, optional): The distance interval in meters to split the route. Defaults to 48000.
        include_end (bool, optional): Whether to include the end point in the result. Defaults to True.

    Returns:
        list[Tuple[str, Coordinates]]: A list of tuples consisting of cache keys and Coordinates objects
        representing the points along the route. This should be in order from beginning to end of the driving
        route.
    """

    points: list[Tuple[str, Coordinates]] = []
    distance: float = 0
    coordinates = directions.features[0].geometry.coordinates
    num_coords = len(coordinates)
    starting_point = Coordinates(coordinates[0], reverse=True)
    points.append((generate_cache_key(starting_point), starting_point))

    for index in range(1, num_coords):
        prev_point = Coordinates(coordinates[index - 1], reverse=True)
        current_point = Coordinates(coordinates[index], reverse=True)

        distance += geodesic(
            (prev_point.lat, prev_point.lon), (current_point.lat, current_point.lon)
        ).meters

        if distance >= interval:
            points.append((generate_cache_key(current_point), current_point))
            distance = 0

    if include_end:
        end_point = Coordinates(coordinates[-1], reverse=True)
        points.append((generate_cache_key(end_point), end_point))

    return points


def get_directions(start: Coordinates, end: Coordinates) -> Directions:
    """
    Retrieves directions between two geographical coordinates.

    Args:
        start: The starting coordinates for the route.
        end: The ending coordinates for the route.

    Returns:
        Directions: A Directions object with the route information.
            Distances are in meters and times are in seconds.
    """

    client: openrouteservice.Client = openrouteservice.Client(
        key=get_key("openroute.key")
    )

    try:
        directions: dict = client.directions(
            ((start.lon, start.lat), (end.lon, end.lat)),
            format="geojson",
            profile="driving-car",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate directions")

    return Directions(directions)


def main():
    directions = get_directions(START, END)
    print(directions)


if __name__ == "__main__":
    main()
