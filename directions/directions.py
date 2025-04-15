import openrouteservice
from fastapi import HTTPException

from directions.models import Coordinates, Directions

"""
This module provides functionality to interact with the OpenRouteService API
for obtaining driving directions between two geographical coordinates. It includes
functions to read an API key, fetch directions from the API, save directions to a
JSON file, and manage stored directions. The module is designed to facilitate 
route planning and navigation tasks by leveraging external routing services.
"""

KEYFILE = "openroute.key"
START = Coordinates((40.25442094053086, -74.68232680066355))
END = Coordinates((40.3156714866853, -74.62401876996654))


def split_directions(
    directions: Directions, interval: int = 25000, include_end: bool = True
) -> list[Coordinates]:
    """
    Splits a given route into a list of coordinates at a specified interval.

    Args:
        directions: The route to split.
        interval: The interval at which to split the route in meters. Defaults to 25km.
        include_end: Whether to include the end of the route in the split points.
            Defaults to True.

    Returns:
        list[Coordinates]: A list of coordinates on the route.
    """

    # Initialize with starting point.
    points: list[Coordinates] = [
        Coordinates(directions.metadata.query.coordinates[0], reverse=True)
    ]

    # Add intermediate points.
    distance = 0
    for idx, step in enumerate(directions.features[0].properties.segments[0].steps):
        if distance > interval:
            points.append(
                Coordinates(
                    directions.features[0].geometry.coordinates[idx], reverse=True
                )
            )
            distance = 0

        distance += step.distance

    if include_end:
        points.append(
            Coordinates(directions.metadata.query.coordinates[1], reverse=True)
        )

    return points


def get_key():
    """
    Reads and returns the API key from the specified key file.

    Returns:
        str: The API key as a string.
    """

    with open(KEYFILE, "r") as f:
        return f.read()


def get_directions(start: Coordinates = START, end: Coordinates = END) -> Directions:
    """
    Retrieves directions between two geographical coordinates.

    Args:
        start: The starting coordinates for the route.
        end: The ending coordinates for the route.

    Returns:
        Directions: A Directions object with the route information.
            Distances are in meters and times are in seconds.
    """

    client: openrouteservice.Client = openrouteservice.Client(key=get_key())

    try:
        directions: dict = client.directions(
            ((start.lon, start.lat), (end.lon, end.lat)),
            format="geojson",
            profile="driving-car",
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Failed to generate directions")
    
    return Directions(directions)


def main():
    directions = get_directions(START, END)
    print(directions)


if __name__ == "__main__":
    main()
