import os
from typing import Any

import requests

LOCATIONIQ_KEY: str | None = os.environ.get("LOCATIONIQ_KEY")
BASE_URL = "https://us1.locationiq.com/v1/search"
HEADERS: dict[str, str] = {"accept": "application/json"}

if LOCATIONIQ_KEY is None:
    raise ValueError("LOCATIONIQ_KEY environment variable is not set")


def get_geo_from_address(address: str) -> dict[str, Any] | None:
    """
    Given a human-readable address, return a LocationIQ address object.

    :param address: A human-readable address.
    :return: A LocationIQ address object or None if the address can't be resolved.
    """
    params: dict = {
        "q": address,
        "key": LOCATIONIQ_KEY,
        "format": "json",
        "limit": 1,
        "normalizeaddress": 1,
        "addressdetails": 1,
    }

    try:
        response: requests.Response = requests.get(
            BASE_URL, params=params, headers=HEADERS
        )
        if response.status_code == 200:
            return response.json()[0]
    except Exception:
        return None
