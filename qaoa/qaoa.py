import pennylane as qml
import numpy as np

class QAOAMaxCut:
    def __init__(self, graph, num_layers=1, steps=20, seed=None, params=None):
        self.graph = graph
        self.num_layers = num_layers
        self.steps = steps
        self.seed = seed
        if seed is not None:
            np.random.seed(seed)
        self.num_wires = max(max(edge) for edge in graph) + 1
        self.dev = qml.device("default.qubit", wires=self.num_wires, shots=None)
        self.params = params
        self.circuit = self._build_qnode()

    def U_B(self, beta):
        for wire in range(self.num_wires):
            qml.RX(2 * beta, wires=wire)

    def U_C(self, gamma):
        for (i, j) in self.graph:
            qml.CNOT(wires=(i, j))
            qml.RZ(gamma, wires=j)
            qml.CNOT(wires=(i, j))

    def objective(self, params):
        gammas, betas = params
        return -0.5 * (len(self.graph) - self.circuit(gammas, betas))

    def _build_qnode(self):
        @qml.qnode(self.dev)
        def circuit(gammas, betas, return_samples=False):
            for w in range(self.num_wires):
                qml.Hadamard(wires=w)

            for gamma, beta in zip(gammas, betas):
                self.U_C(gamma)
                qml.Snapshot()
                self.U_B(beta)
                qml.Snapshot()

            if return_samples:
                return qml.sample()

            C = qml.sum(*(qml.Z(i) @ qml.Z(j) for i, j in self.graph))
            return qml.expval(C)

        return circuit


    def run(self):
        # if self.params is None:
        #     init = 0.01 * np.random.rand(2, self.num_layers)
        #     init.setflags(write=True)
        #     self.params = init.copy()
        #     opt = qml.AdagradOptimizer(stepsize=0.5)
        #     for _ in range(self.steps):
        #         self.params = opt.step(self.objective, self.params)
        snaps = qml.snapshots(self.circuit)(*self.params)
        return self.circuit, self.params, snaps
