import os

import requests

LOCATIONIQ_KEY = os.environ.get("LOCATIONIQ_KEY")
BASE_URL = "https://us1.locationiq.com/v1/search"
HEADERS = {"accept": "application/json"}


def get_geo_from_address(address: str) -> dict:
    """
    Geocode a given address using LocationIQ.

    Args:
        address: The address to geocode.

    Returns:
        A single dictionary containing the geocoded information.
    """
    params: dict = {
        "q": address,
        "key": LOCATIONIQ_KEY,
        "format": "json",
        "limit": 1,
        "normalizeaddress": 1,
        "addressdetails": 1,
    }

    response = requests.get(BASE_URL, params=params, headers=HEADERS)

    if response.status_code == 200:
        return response.json()[0]
