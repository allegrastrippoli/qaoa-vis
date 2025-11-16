import matplotlib.pyplot as plt
from pennylane import numpy as np
import pennylane as qml
import numpy as np
import cmath
import math
import json
import os

np.random.seed(42)
output_dir = "./charts" 
plot_subdirs = [f"{output_dir}/state_probability", 
                f"{output_dir}/state_phase", 
                f"{output_dir}/state_probability_aggregate", 
                f"{output_dir}/state_phase_aggregate",
                f"{output_dir}/probability_phase",
                f"{output_dir}/probability_phase_aggregate",
                f"{output_dir}/heatmap"]
os.makedirs(output_dir, exist_ok=True) 
for path in plot_subdirs:
    os.makedirs(path, exist_ok=True)

def draw_circuit(circuit, params):
    qml.drawer.use_style("black_white")
    fig, ax = qml.draw_mpl(circuit)(*params)
    file_path = os.path.join(f" {output_dir}", f"circuit.png")
    plt.savefig(file_path, dpi=300, format='png')

def list_multiplication(base, n):
    return [base] * (n)

def get_min_max(metric_dict):
    all_values = []
    for values in metric_dict.values():
        all_values.extend(values)  
    return min(all_values), max(all_values)

def run_qaoa_for_graph(graph, num_layers=1, steps=20, seed=None, params=None):
    if seed is not None:
        np.random.seed(seed)
        
    num_wires = max(max(edge) for edge in graph) + 1
    dev = qml.device("default.qubit", wires=num_wires, shots=None)

    def U_B(beta):
        for wire in range(num_wires):
            qml.RX(2 * beta, wires=wire)

    def U_C(gamma):
        for edge in graph:
            qml.CNOT(wires=edge)
            qml.RZ(gamma, wires=edge[1])
            qml.CNOT(wires=edge)
            
    @qml.qnode(dev)
    def circuit(gammas, betas, return_samples=False):
        for wire in range(num_wires):
            qml.Hadamard(wires=wire)
        # qml.Snapshot()
        for gamma, beta in zip(gammas, betas):
            U_C(gamma)
            qml.Snapshot()
            U_B(beta)
            qml.Snapshot()
        if return_samples:
            return qml.sample()
        C = qml.sum(*(qml.Z(w1) @ qml.Z(w2) for w1, w2 in graph))
        return qml.expval(C)

    def objective(params):
        return -0.5 * (len(graph) - circuit(*params))

    if params is None:
        init_params = 0.01 * np.random.rand(2, num_layers, requires_grad=True)
        opt = qml.AdagradOptimizer(stepsize=0.5)
        params = init_params.copy()
        for _ in range(steps):
            params = opt.step(objective, params)

    snaps = qml.snapshots(circuit)(*params)
    return circuit, params, snaps

def prepare_fig(metric_dict, num_plots,  y_label, y_range_bool, sharey=True):
    if y_range_bool:
        y_min, y_max = get_min_max(metric_dict)
        padding = 0.1 * (y_max - y_min)
        y_range = (y_min - padding, y_max + padding)
        
    cols = math.ceil(math.sqrt(num_plots))
    rows = math.ceil(num_plots / cols)
    fig, axes = plt.subplots(rows, cols, figsize=(5 * cols, 4 * rows), sharey=sharey)

    if num_plots == 1:
        axes = [axes]
    else:
        axes = axes.flatten()

    for ax in axes:
        ax.set_xlabel("state")
        ax.set_ylabel(y_label)
        ax.grid(True)
        if y_range:
            ax.set_ylim(y_range)

    return fig, axes, y_range

def state_metric_aggregate(file_path, states, metric_dict, n_snapshots,
                                            fixed_params, y_label, y_range_bool=True):
    fig, axes, y_range = prepare_fig(
        metric_dict=metric_dict,
        num_plots=n_snapshots,
        y_label=y_label,
        y_range_bool=y_range_bool
    )

    results = []    
    results.append({
        "Y range": y_range,
        "Period" : len(fixed_params),
        "Fixed parameters": list(fixed_params)
    })
    for i in range(n_snapshots):
        ax = axes[i]
        j = i
        series_num = 0
        while j in metric_dict:
            y = metric_dict[j]
            results.append({
            "State": states,
            "Metric": y
            })        
            ax.plot(states, y, label=f"γ,β={abs(round(fixed_params[series_num], 3))}") 
            # !!!!!!!!!!!!!!!!!!
            j += n_snapshots
            series_num += 1

        ax.set_xticks(range(len(states)))
        ax.set_xticklabels(states, rotation=90)
        ax.legend()
    
    with open(file_path.replace("svg", "json"), "w") as f:
        json.dump(results, f, indent=4)

    fig.suptitle(y_label)
    fig.tight_layout()
    plt.savefig(file_path, dpi=300, format=file_path.split('.')[-1])
    plt.close(fig)
  
def state_metric(file_path, states, metric_dict, y_label,
                               line_color="#5891F3", y_range_bool=True):
    
    fig, axes, y_range = prepare_fig(
        num_plots=len(metric_dict),
        metric_dict=metric_dict,
        y_label=y_label,
        y_range_bool=y_range_bool
    )

    for ax, (label, values) in zip(axes, metric_dict.items()):
        ax.plot(states, list(values), color=line_color, linestyle='-', marker='o')
        ax.set_xticks(range(len(states)))
        ax.set_xticklabels(states, rotation=90)
        ax.set_title(label)

    fig.suptitle(y_label)
    fig.tight_layout()
    # plt.subplots_adjust(right=1)
    plt.savefig(file_path, dpi=300, format=file_path.split('.')[-1])
    plt.close(fig)
    
def from_snapshot_to_values(snaps, save_json=False):
     # dict size: 
     # there are "n_snapshots" keys
     # for each snapshot, there are "2^num_wires" values 
    probs = dict() # { snapshot id: list of probabilities }
    phases = dict()   
    for i in range(len(snaps)-1):
        probs[i] = []
        phases[i] = []
        for n in snaps[i]:
            p = np.abs(n)**2 # For complex input the absolute value is rad(a^2+b^2)     
            probs[i].append((p.tolist()))
            phases[i].append(cmath.phase(n))
            
    # print(f"Probs: {probs}")
    # print(f"Phases: {phases}")
    if save_json:
        results = []
        results.append({
            "Probabilities": probs,
            "Phases": phases,
        })
        with open(f"{output_dir}/probability_phase.json", "w") as f:
            json.dump(results, f, indent=4)
            
    return probs, phases


def prepare_prob_phase_fig(states, probs_list, phases_list):
    cols = math.ceil(math.sqrt(len(states)))
    rows = math.ceil(len(states) / cols)
    fig, axes = plt.subplots(rows, cols, figsize=(8 * cols, 4 * rows))

    if len(states) == 1:
        axes = [axes]
    else:
        axes = axes.flatten()

    all_x = [x for sublist in probs_list for x in sublist]
    all_y = [y for sublist in phases_list for y in sublist]
    x_min, x_max = min(all_x), max(all_x)
    y_min, y_max = min(all_y), max(all_y)

    x_padding = (x_max - x_min) * 0.05
    y_padding = (y_max - y_min) * 0.05

    x_range = (x_min - x_padding, x_max + x_padding)
    y_range = (y_min - y_padding, y_max + y_padding)

    return fig, axes, x_range, y_range

def probability_phase(file_path, states, probs_list, phases_list):
    fig, axes, x_range, y_range = prepare_prob_phase_fig(states, probs_list, phases_list)

    for i, state in enumerate(states):
        ax = axes[i]
        x = probs_list[i]
        y = phases_list[i]
        colors = ['green', 'red']

        for j in range(len(x) - 1):
            ax.annotate(
                '',
                xy=(x[j + 1], y[j + 1]),
                xytext=(x[j], y[j]),
                arrowprops=dict(arrowstyle='->', color=colors[j % 2])
            )
            ax.plot(x[j], y[j], 'o', color=colors[j % 2])

        ax.plot(x[0], y[0], 'o', color='yellow', markersize=8, markeredgecolor='black', label='Start')
        ax.plot(x[-1], y[-1], 'o', color='orange', markersize=8, markeredgecolor='black', label='End')

        ax.plot([], [], color='black', label=f'State {state}')
        ax.set_xlabel('Probability')
        ax.set_ylabel('Phase')
        ax.grid()
        ax.legend()
        ax.set_xlim(*x_range)
        ax.set_ylim(*y_range)

    for j in range(len(states), len(axes)):
        fig.delaxes(axes[j])

    plt.tight_layout()
    plt.savefig(file_path, dpi=300, format=file_path.split('.')[-1])
    plt.close(fig)
    
def probability_phase_aggregate(file_path, states, probs_list, phases_list, fixed_params):
    n_snapshots = len(fixed_params)
    fig, axes, x_range, y_range = prepare_prob_phase_fig(states, probs_list, phases_list)
    
    results = []  
    
    for i, state in enumerate(states):
        ax = axes[i]
        values = []
        for j in range(n_snapshots):
            idx = i + len(states) * j
            x = probs_list[idx]
            y = phases_list[idx]
            values.append({
            "Probability": list(x),
            "Phase": list(y)
            })   
            ax.plot(x, y, '<-', label=round(fixed_params[j], 3))

            ax.plot(x[0], y[0], 'o', color='yellow', markersize=8, markeredgecolor='black', label='Start' if j == 0 else "")
            ax.plot(x[-1], y[-1], 'o', color='orange', markersize=8, markeredgecolor='black', label='End' if j == 0 else "")
        results.append({
            "State": state,
            "Values": values})

        ax.plot([], [], color='black', label=f'State {state}')
        ax.set_xlabel('Probability')
        ax.set_ylabel('Phase')
        ax.grid()
        ax.legend()
        ax.set_xlim(*x_range)
        ax.set_ylim(*y_range)

    for j in range(len(states), len(axes)):
        fig.delaxes(axes[j])
        
    with open(file_path.replace("svg", "json"), "w") as f:
        json.dump(results, f, indent=4)

    plt.tight_layout()
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    plt.savefig(file_path, dpi=300, format=file_path.split('.')[-1])
    plt.close(fig)
 
def from_state_to_values(states, snaps, num_wires, save_json=False):
     # list size: 
     # 2^num_wires states
     # for each state, there are "n_snapshots" values 
    shape = list_multiplication(2, num_wires)
    probs_list = []  # [[probabilities for state 0], [probabilities for state 1], ... ]
    phases_list = []
    states_list = [[int(bit) for bit in state] for state in states]
    
    for state in states_list:
        probs = np.zeros(len(snaps) - 1)
        phases = np.zeros(len(snaps) - 1)
        for i in range(len(snaps) - 1):
            if len(state) != len(shape):
                raise ValueError("Wrong shape")
            amplitude = snaps[i].reshape(*shape)[tuple(state)]
            probs[i] = np.abs(amplitude) ** 2
            phases[i] = cmath.phase(amplitude)

        probs_list.append(probs)
        phases_list.append(phases)
        
        # print(f"State: {state}, Probabilities: {probs}, Phases: {phases}")
    if save_json:
        results = []
        results.append({
    "State": state,
    "Probabilities": probs.tolist(),
    "Phases": phases.tolist()
})     
        with open(f"{output_dir}/probability_phase.json", "w") as f:
            json.dump(results, f, indent=4)
        
    return probs_list, phases_list

def collect_states(edges, num_layers, num_wires, states,  gamma_vals = None, beta_vals = None):
    all_probs, all_phases = [], []
    for gamma, beta in zip(gamma_vals, beta_vals):
        circuit, params, snaps = run_qaoa_for_graph(
            edges, num_layers=num_layers,
            params=[[gamma] * num_layers, [beta] * num_layers]
        )
        probs_list, phases_list = from_state_to_values(states, snaps, num_wires)
        all_probs.extend(probs_list)
        all_phases.extend(phases_list)
    return all_probs, all_phases

def collect_snapshots(edges, num_layers, gamma_vals=None, beta_vals=None):
    all_probs, all_phases = {}, {}
    key_offset, n_snapshots = 0, 0
    for gamma, beta in zip(gamma_vals, beta_vals):
        circuit, params, snaps = run_qaoa_for_graph(
            edges, num_layers=num_layers,
            params=[[gamma] * num_layers, [beta] * num_layers]
        )
        probs_dict, phases_dict = from_snapshot_to_values(snaps)
        n_snapshots = len(probs_dict)
        for k, v in probs_dict.items():
            all_probs[key_offset + k] = v
        for k, v in phases_dict.items():
            all_phases[key_offset + k] = v
        key_offset += n_snapshots
    return all_probs, all_phases, n_snapshots
    
def run_plot_engine(
    filename, num_layers, num_wires, edges, states,
     gamma_vals=None, beta_vals=None, aggregate=False,
    from_snapshot_to_values_bool=False,
    from_state_to_values_bool=False
):
    # if gamma_vals is not None and beta_vals is not None:
        if from_snapshot_to_values_bool:
            if aggregate:
                all_probs, all_phases, n_snapshots = collect_snapshots(edges, num_layers, gamma_vals, beta_vals)
                state_metric_aggregate(
                    f"{plot_subdirs[2]}/{plot_subdirs[2].split('/')[-1]}.svg", states, all_probs, n_snapshots, gamma_vals, plot_subdirs[2].split('_')[1]
                )
                state_metric_aggregate(
                    f"{plot_subdirs[3]}/{plot_subdirs[3].split('/')[-1]}.svg", states, all_phases, n_snapshots, gamma_vals, plot_subdirs[3].split('_')[1]
                )
            # else: 
            #     circuit, params, snaps = run_qaoa_for_graph(edges, num_layers=num_layers, params=gamma_vals)
            #     probs, phases = from_snapshot_to_values(snaps)
            #     state_metric(f"{plot_subdirs[0]}/{filename}", states, probs, plot_subdirs[0].split('_')[1], line_color="orange")
            #     state_metric(f"{plot_subdirs[1]}/{filename}", states, phases, plot_subdirs[1].split('_')[1])
                
        elif from_state_to_values_bool:
            if aggregate:
                all_probs, all_phases = collect_states(edges, num_layers, num_wires, states,  gamma_vals, beta_vals)
                probability_phase_aggregate(f"{plot_subdirs[5]}/{plot_subdirs[5].split('/')[-1]}.svg", states, all_probs, all_phases, gamma_vals)
            # else:
            #     circuit, params, snaps = run_qaoa_for_graph(edges, num_layers=num_layers, params=gamma_vals)
            #     probs, phases = from_state_to_values(states, snaps, num_wires)
            #     probability_phase(f"{plot_subdirs[4]}/{filename}", states, probs, phases)


# def test_gamma_beta_incremental(num_layers, num_wires, edges, states):
#     gamma_vals = -np.arange(0.01, 0.09, 0.01)
#     beta_vals  =  np.arange(0.01, 0.09, 0.01)
#     if len(gamma_vals) == len(beta_vals):
#         for i in range(len(gamma_vals)):
#             params = [[gamma_vals[i]]*num_layers, [beta_vals[i]]*num_layers]
#             run_plot_engine(f"example_graph{i}.svg", num_layers, num_wires, edges, states, params, None, aggregate=False, from_snapshot_to_values_bool=True)
#             run_plot_engine(f"example_graph{i}.svg", num_layers, num_wires, edges, states, params, None, aggregate=False, from_state_to_values_bool=True)

def test_gamma_beta_aggregate_incremental(num_layers, num_wires, edges, states):
    gamma_vals = -np.arange(0.01, 0.09, 0.01)
    beta_vals  =  np.arange(0.01, 0.09, 0.01)
    if len(gamma_vals) == len(beta_vals):
        run_plot_engine(f"example_graph.svg", num_layers, num_wires, edges, states, gamma_vals, beta_vals, aggregate=True, from_snapshot_to_values_bool=True)    
        run_plot_engine(f"example_graph.svg", num_layers, num_wires, edges, states, gamma_vals, beta_vals, aggregate=True, from_state_to_values_bool=True)
    
if __name__ == "__main__":
    num_layers = 2
    edges = []
    nodes = set()
    with open("graph.txt") as f:
        for line in f:
            node1 = int(line.split(',')[0])
            node2 = int(line.split(',')[1])
            edges.append((node1,node2))
            nodes.add(node1)
            nodes.add(node2)
    num_wires = len(nodes)
    states = [format(i, f'0{num_wires}b') for i in range(2 ** num_wires)]   
    # test_gamma_beta_incremental(num_layers, num_wires, edges, states)
    test_gamma_beta_aggregate_incremental(num_layers, num_wires, edges, states)

