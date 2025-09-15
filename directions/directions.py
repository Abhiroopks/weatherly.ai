import os

import openrouteservice
from fastapi import HTTPException
from geopy.distance import geodesic

from models.core import Coordinate
from models.directions import Directions

"""
This module provides functionality to interact with the OpenRouteService API
for obtaining driving directions between two geographical coordinates. It includes
functions to read an API key, fetch directions from the API, save directions to a
JSON file, and manage stored directions. The module is designed to facilitate 
route planning and navigation tasks by leveraging external routing services.
"""

CLIENT: openrouteservice.Client = openrouteservice.Client(
    key=os.getenv("OPENROUTE_KEY")
)


def split_directions(
    directions: Directions, interval: int = 48000, include_end: bool = True
) -> list:
    """
    Split driving directions into a list of coordinates spaced at a given interval.

    The function takes in a Directions object and returns a list of Coordinate objects.
    The coordinates are spaced at a given interval (in meters) along the route.

    Parameters
    ----------
    directions : Directions
        A Directions object representing the route.
    interval : int, optional
        The interval (in meters) at which to split the route. Defaults to 48000.
    include_end : bool, optional
        Whether to include the final coordinate of the route in the output. Defaults to True.

    Returns
    -------
    list
        A list of Coordinate objects representing the split route.
    """
    points: list = []
    distance: float = 0
    coordinates = directions.features[0].geometry.coordinates  # type: ignore
    num_coords = len(coordinates)

    starting_point = Coordinate(lat=coordinates[0][1], lon=coordinates[0][0])

    points.append(starting_point)

    for index in range(1, num_coords):
        prev_point = Coordinate(
            lat=coordinates[index - 1][1], lon=coordinates[index - 1][0]
        )
        current_point = Coordinate(lat=coordinates[index][1], lon=coordinates[index][0])

        distance += geodesic(
            (prev_point.lat, prev_point.lon), (current_point.lat, current_point.lon)
        ).meters

        if distance >= interval:
            points.append(current_point)
            distance = 0

    if include_end:
        end_point = Coordinate(lat=coordinates[-1][1], lon=coordinates[-1][0])
        points.append(end_point)

    return points


def get_directions(start: Coordinate, end: Coordinate) -> Directions:
    """
    Retrieves directions between two geographical coordinates.

    Args:
        start: The starting coordinates for the route.
        end: The ending coordinates for the route.

    Returns:
        Directions: A Directions object with the route information.
            Distances are in meters and times are in seconds.
    """

    try:
        directions: dict = CLIENT.directions(  # type: ignore
            ((start.lon, start.lat), (end.lon, end.lat)),
            format="geojson",
            profile="driving-car",
        )
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to generate directions")

    return Directions(directions)
