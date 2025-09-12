"""
Data model definitions
"""

import json


class DictObj:
    def __init__(self, in_dict: dict) -> None:
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

    def __str__(self) -> str:
        """
        Return a JSON formatted string of the object.

        :return: A string with the object's attributes in JSON format
        :rtype: str
        """
        return json.dumps(self.__dict__, default=lambda o: o.__dict__, indent=4)


class Coordinate:
    def __init__(self, lat: float, lon: float) -> None:
        if isinstance(lat, str):
            lat = float(lat)
        if isinstance(lon, str):
            lon = float(lon)

        self.lat: float = lat
        self.lon: float = lon
