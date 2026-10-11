# solution_tfim_simulation/src/routing.py
"""
Transpilation and routing analysis module.
Maps logical quantum circuits to physical coupling maps and analyzes SWAP overhead.
"""

from typing import Dict, Any, Optional
from qiskit import QuantumCircuit, transpile
from qiskit.transpiler import CouplingMap
from .metrics import circuit_metrics


def transpile_for_processor(
    circuit: QuantumCircuit,
    proc: Dict[str, Any],
    optimization_level: int = 1,
    seed_transpiler: int = 42,
    initial_layout: Optional[list] = None
) -> QuantumCircuit:
    """
    Transpiles a logical quantum circuit onto the target processor architecture.
    """
    cmap = CouplingMap(proc["coupling_map"])
    return transpile(
        circuit,
        coupling_map=cmap,
        basis_gates=proc.get("basis_gates", ["rz", "sx", "x", "cx"]),
        optimization_level=optimization_level,
        seed_transpiler=seed_transpiler,
        initial_layout=initial_layout
    )


def analyze_routing_overhead(
    logical_circuit: QuantumCircuit,
    transpiled_circuit: QuantumCircuit
) -> Dict[str, Any]:
    """
    Analyzes the overhead introduced by routing and decomposition:
    - delta depth
    - depth expansion ratio
    - additional two-qubit operations (routing SWAP overhead)
    - total operation delta
    """
    log_m = circuit_metrics(logical_circuit)
    trans_m = circuit_metrics(transpiled_circuit)

    delta_depth = trans_m["depth"] - log_m["depth"]
    depth_ratio = trans_m["depth"] / log_m["depth"] if log_m["depth"] > 0 else 1.0
    two_q_overhead = trans_m["two_qubit_ops_estimate"] - log_m["two_qubit_ops_estimate"]
    total_ops_overhead = trans_m["total_ops"] - log_m["total_ops"]

    return {
        "logical_depth": log_m["depth"],
        "transpiled_depth": trans_m["depth"],
        "delta_depth": delta_depth,
        "depth_expansion_ratio": round(depth_ratio, 3),
        "logical_two_q_ops": log_m["two_qubit_ops_estimate"],
        "transpiled_two_q_ops": trans_m["two_qubit_ops_estimate"],
        "two_q_overhead": two_q_overhead,
        "swaps_inserted": trans_m["swap_count"],
        "total_ops_overhead": total_ops_overhead,
    }
