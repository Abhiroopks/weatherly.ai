import json


def load_json(file_path: str) -> dict | list:
    with open(file_path, "r") as f:
        return json.load(f)
