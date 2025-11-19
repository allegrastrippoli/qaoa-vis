import cmath 
import numpy as np

class DataProcessor:
    def __init__(self, snaps):
        self.snaps = snaps

    def get_values_from_snaps(self):
        key_offset = 0
        all_probs, all_phases = {}, {}
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
        n_snapshots = len(probs)
        for k, v in probs.items():
            all_probs[key_offset + k] = v
        for k, v in phases.items():
            all_phases[key_offset + k] = v
        key_offset += n_snapshots
        return all_probs, all_phases, n_snapshots
