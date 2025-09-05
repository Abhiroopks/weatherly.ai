import os

import openrouteservice
from fastapi import HTTPException
from geopy.distance import geodesic

from directions.models import Coordinates, Directions

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
) -> list[Coordinates]:
    points: list[Coordinates] = []
    distance: float = 0
    coordinates = directions.features[0].geometry.coordinates  # type: ignore
    num_coords = len(coordinates)
    starting_point = Coordinates(coordinates[0], reverse=True)
    points.append(starting_point)

    for index in range(1, num_coords):
        prev_point = Coordinates(coordinates[index - 1], reverse=True)
        current_point = Coordinates(coordinates[index], reverse=True)

        distance += geodesic(
            (prev_point.lat, prev_point.lon), (current_point.lat, current_point.lon)
        ).meters

        if distance >= interval:
            points.append(current_point)
            distance = 0

    if include_end:
        end_point = Coordinates(coordinates[-1], reverse=True)
        points.append(end_point)

    print(f"Generated {len(points)} points from directions")
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

    try:
        directions: dict = CLIENT.directions(  # type: ignore
            ((start.lon, start.lat), (end.lon, end.lat)),
            format="geojson",
            profile="driving-car",
        )
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to generate directions")

    return Directions(directions)
