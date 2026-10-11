# solution_tfim_simulation/src/metrics.py
"""
Resource and performance metrics computation according to Phase 1 Guide specifications.
"""

import math
from typing import Dict, Any
from qiskit import QuantumCircuit


TWO_Q_GATE_NAMES = {"cx", "cz", "ecr", "swap", "rxx", "ryy", "rzz", "iswap"}


def circuit_metrics(qc: QuantumCircuit) -> Dict[str, Any]:
    """
    Computes architecture resource metrics for a transpiled QuantumCircuit:
    - depth
    - num_qubits (physical qubit footprint)
    - total_ops
    - two_qubit_ops_estimate
    - swap_count
    - operations breakdown
    """
    ops = qc.count_ops()
    return {
        "depth": int(qc.depth()),
        "num_qubits": int(qc.num_qubits),
        "total_ops": int(sum(ops.values())),
        "two_qubit_ops_estimate": int(
            sum(n for g, n in ops.items() if g.lower() in TWO_Q_GATE_NAMES)
        ),
        "swap_count": int(ops.get("swap", 0)),
        "operations": dict(ops),
    }


def proportion_standard_error(p: float, n: int) -> float:
    """
    Computes the binomial standard error for an estimated proportion / yield:
    sigma_p = sqrt(p * (1 - p) / n)
    """
    if n <= 0 or p < 0.0 or p > 1.0:
        return 0.0
    return math.sqrt(p * (1.0 - p) / n)


def energy_error(e_computed: float, e_exact: float) -> float:
    """
    Computes absolute error in ground state energy: |E_computed - E_exact|
    """
    return float(abs(e_computed - e_exact))
