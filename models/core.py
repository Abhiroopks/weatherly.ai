"""
Data model definitions
"""


class Coordinate:
    def __init__(self, lat: float, lon: float) -> None:
        if isinstance(lat, str):
            lat = float(lat)
        if isinstance(lon, str):
            lon = float(lon)

        self.lat: float = lat
        self.lon: float = lon
