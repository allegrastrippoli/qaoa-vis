import cmath 
import numpy as np

class DataProcessor:
    def __init__(self, snaps):
        self.snaps = snaps

    def get_values_from_snaps(self):
        # dict size: 
        # there are "n_snapshots" keys
        # for each snapshot, there are "2^num_wires" values 
        probs = dict() # { snapshot id: list of probabilities }
        phases = dict()   
        for i in range(len(self.snaps)-1):
            probs[i] = []
            phases[i] = []
            for n in self.snaps[i]:
                p = np.abs(n)**2 # For complex input the absolute value is rad(a^2+b^2)     
                probs[i].append((p.tolist()))
                phases[i].append(cmath.phase(n))
        # print(f"Probs: {probs}")
        # print(f"Phases: {phases}")
        return probs, phases 
    
    def get_min_max(self, metric_dict):
        all_values = []
        for values in metric_dict.values():
            all_values.extend(values)  
        return min(all_values), max(all_values)
    
    def get_y_range(self, metric_dict):
        y_min, y_max = self.get_min_max(metric_dict)
        padding = 0.1 * (y_max - y_min)
        return (y_min - padding, y_max + padding)
    

    def get_data_per_layer(self, states, metric_dict, n_snapshots):
        data_per_layer = dict() # key: num_layer, value: list of values
        for i in range(n_snapshots):
            j = i
            while j in metric_dict:
                if i in data_per_layer:
                    data_per_layer[i].append(metric_dict[j])
                else: 
                    data_per_layer[i] = []
                    data_per_layer[i].append(metric_dict[j])
                j += n_snapshots
        return data_per_layer
   