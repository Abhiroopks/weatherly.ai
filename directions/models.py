"""
Data model definitions
"""

import json

import geohash
from pydantic import BaseModel


class Coordinates(BaseModel):
    """
    Coordinates class

    Attributes:
        lat (float): The latitude
        lon (float): The longitude
    """

    def __init__(self, coordinates: tuple[float, float], reverse: bool = False):
        super().__init__(
            lat=coordinates[1] if reverse else coordinates[0],
            lon=coordinates[0] if reverse else coordinates[1],
        )

    lat: float
    lon: float


def generate_cache_key(loc: Coordinates) -> str:
    """
    Generate a cache key using geohash encoding from a Coordinates object.
    This function encodes the given geographical coordinates into a geohash
    string with a precision of 5, which corresponds to about 5km x 5km block.
    Args:
        loc (Coordinates): The location for which to generate a cache key.
    Returns:
        str: A geohash string used as the cache key.
    """
    geohash_key = geohash.encode(loc.lat, loc.lon, precision=5)
    return geohash_key


class DictObj:
    def __init__(self, in_dict: dict):
        """
        Initialize the object from a dictionary.

        Recursively transforms the input dictionary into an object
        with attributes that correspond to the keys in the dictionary.
        If a value is a list or tuple, it will be converted to a list
        of objects. If a value is a dictionary, it will be converted
        to an object recursively.

        :param in_dict: The dictionary to convert to an object
        :type in_dict: dict
        """
        assert isinstance(in_dict, dict)
        for key, val in in_dict.items():
            if isinstance(val, (list, tuple)):
                setattr(
                    self, key, [DictObj(x) if isinstance(x, dict) else x for x in val]
                )
            else:
                setattr(self, key, DictObj(val) if isinstance(val, dict) else val)

    def __str__(self):
        """
        Return a JSON formatted string of the object.

        :return: A string with the object's attributes in JSON format
        :rtype: str
        """
        return json.dumps(self.__dict__, default=lambda o: o.__dict__, indent=4)


class Directions(DictObj):
    pass
