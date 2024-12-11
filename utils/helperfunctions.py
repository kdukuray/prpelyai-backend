import json

def is_valid_json(string: str) -> bool:
    try:
        json.loads(string)
        return True
    except ValueError:
        return False

# def combine