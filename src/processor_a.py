# solution_tfim_simulation/src/processor_a.py
"""
Dedicated module for Processor A (5-Qubit Fixed Baseline, T-Tree Topology).
Encapsulates coupling map, graph definition, custom layout coordinates, and noise model.
"""

from typing import Dict, Any, List, Tuple
from pathlib import Path
import json
import networkx as nx
from qiskit.transpiler import CouplingMap
from .processors import load_processor, build_noise_model


class ProcessorA:
    """
    Processor A: 5-Qubit Online Fixed Baseline
    Topology: T-Tree (Node 0 is the central junction connected to 1, 2, 3; node 3 connects to 4).
    """
    def __init__(self, config_path: str = "solution_tfim_simulation/processors/processor_A.json"):
        p = Path(config_path)
        if not p.exists():
            # Fallback path if running from within solution_tfim_simulation/
            p = Path("processors/processor_A.json")
        self.config = load_processor(str(p))
        self.name = self.config["name"]
        self.num_qubits = self.config["num_qubits"]
        self.coupling_map = self.config["coupling_map"]
        self.basis_gates = self.config.get("basis_gates", ["rz", "sx", "x", "cx"])
        self.noise_config = self.config.get("noise", {})

        # Visual layout coordinates matching challenge guide slide
        self.layout_pos = {
            0: (0.0, 1.0),   # Top junction
            1: (-0.6, 0.4),  # Left branch
            2: (0.6, 0.4),   # Right branch
            3: (0.0, 0.1),   # Trunk middle
            4: (0.0, -0.6)   # Trunk bottom
        }

    def get_coupling_map(self) -> CouplingMap:
        """Returns Qiskit CouplingMap instance."""
        return CouplingMap(self.coupling_map)

    def get_graph(self) -> nx.Graph:
        """Returns NetworkX Graph instance."""
        G = nx.Graph()
        G.add_nodes_from(range(self.num_qubits))
        G.add_edges_from(map(tuple, self.coupling_map))
        return G

    def get_noise_model(self):
        """Builds and returns the challenge synthetic noise model."""
        return build_noise_model(
            single_q_error=self.noise_config.get("single_qubit_depolarizing", 0.001),
            two_q_error=self.noise_config.get("two_qubit_depolarizing", 0.01),
            readout_error_matrix=self.noise_config.get("readout_error", [[0.99, 0.01], [0.02, 0.98]])
        )
