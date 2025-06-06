def get_key(file: str) -> str:
    """
    Reads and returns the API key from the specified key file.

    Returns:
        str: The API key as a string.
    """

    with open(file, "r") as f:
        return f.read()
