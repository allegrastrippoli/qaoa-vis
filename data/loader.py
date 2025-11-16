import json
import os

def load_json(path):
    with open(path) as f:
        data = json.load(f)
    return data[0], data[1:]

def load_edges(path):
    try:
        with open(path) as f:
            return [tuple(map(int, line.strip().split(','))) for line in f]
    except FileNotFoundError:
        return []
