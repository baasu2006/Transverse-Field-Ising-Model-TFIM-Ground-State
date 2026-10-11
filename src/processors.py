# solution_tfim_simulation/src/processors.py
"""
Processor graph representation, loader, and synthetic noise model generator.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
import networkx as nx
from qiskit.transpiler import CouplingMap
from qiskit_aer.noise import NoiseModel, depolarizing_error, ReadoutError


def load_processor(path: str) -> Dict[str, Any]:
    """
    Loads processor architecture specification from a JSON file.
    """
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Processor file not found: {path}")
    with file_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def build_processor_graph(proc: Dict[str, Any]) -> nx.Graph:
    """
    Constructs a NetworkX graph representation of the processor coupling map.
    """
    G = nx.Graph()
    G.add_nodes_from(range(proc["num_qubits"]))
    G.add_edges_from(map(tuple, proc["coupling_map"]))
    return G


def get_coupling_map(proc: Dict[str, Any]) -> CouplingMap:
    """
    Returns Qiskit CouplingMap instance.
    """
    return CouplingMap(proc["coupling_map"])


def build_noise_model(
    single_q_error: float = 0.001,
    two_q_error: float = 0.01,
    readout_error_matrix: Optional[list] = None
) -> NoiseModel:
    """
    Builds the official challenge synthetic noise model:
    - 1-qubit depolarizing error on single-qubit gates ('x', 'sx')
    - 2-qubit depolarizing error on two-qubit gates ('cx')
    - Readout error on measurements
    """
    if readout_error_matrix is None:
        readout_error_matrix = [[0.99, 0.01], [0.02, 0.98]]

    noise_model = NoiseModel()
    # 1-qubit depolarizing error
    noise_model.add_all_qubit_quantum_error(
        depolarizing_error(single_q_error, 1), ["x", "sx"]
    )
    # 2-qubit depolarizing error
    noise_model.add_all_qubit_quantum_error(
        depolarizing_error(two_q_error, 2), ["cx"]
    )
    # Readout error
    noise_model.add_all_qubit_readout_error(
        ReadoutError(readout_error_matrix)
    )

    return noise_model
