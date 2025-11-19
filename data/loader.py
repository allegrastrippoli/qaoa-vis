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

def write_values(path, n_snapshots, y_range, fixed_params, states, metric_dict):
    results = []    
    results.append({
        "Y range": y_range,
        "Period" : len(fixed_params),
        "Fixed parameters": list(fixed_params)
    })    
    for i in range(n_snapshots):
        j = i
        while j in metric_dict:
            y = metric_dict[j]
            results.append({
            "State": states,
            "Metric": y
            })   
            j += n_snapshots
            
    with open(path, "w") as f:
        json.dump(results, f, indent=4)
    
