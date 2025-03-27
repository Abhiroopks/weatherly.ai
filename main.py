import json
from directions.directions import get_directions, split_directions
from directions.models import Directions

def read_directions(fname: str) -> Directions:
    """
    Reads a JSON file and returns a Directions object.

    :param fname: The path to the JSON file to read.
    :return: A Directions object.
    """
    with open(fname, "r") as f:
        return Directions(json.load(f))

def main():
    #directions = get_directions()
    directions = read_directions("directions.json")
    weather_points = split_directions(directions, interval=2000)

    for point in weather_points:
        print(f"{point}\n")


if __name__ == "__main__":
    main()
