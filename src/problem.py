# solution_tfim_simulation/src/problem.py
"""
Transverse-Field Ising Model (TFIM) ground state problem formulation,
classical exact diagonalization solver, and parameterized VQE ansatz.
"""

from typing import List, Tuple
import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit.library import efficient_su2
from qiskit.quantum_info import SparsePauliOp


def build_tfim_hamiltonian(N: int, J: float = 1.0, h: float = 1.0) -> np.ndarray:
    """
    Builds the explicit dense matrix representation of the TFIM Hamiltonian:
    H = -J * sum_{i=0}^{N-2} (Z_i * Z_{i+1}) - h * sum_{i=0}^{N-1} X_i
    """
    I = np.eye(2, dtype=complex)
    X = np.array([[0, 1], [1, 0]], dtype=complex)
    Z = np.array([[1, 0], [0, -1]], dtype=complex)

    def kron_list(ops):
        res = ops[0]
        for op in ops[1:]:
            res = np.kron(res, op)
        return res

    H = np.zeros((2**N, 2**N), dtype=complex)

    # Nearest-neighbor ZZ interaction
    for i in range(N - 1):
        ops = [I] * N
        ops[i] = Z
        ops[i + 1] = Z
        H += -J * kron_list(ops)

    # Transverse magnetic field X
    for i in range(N):
        ops = [I] * N
        ops[i] = X
        H += -h * kron_list(ops)

    return H


def exact_ground_energy(N: int, J: float = 1.0, h: float = 1.0) -> float:
    """
    Computes exact ground-state energy via exact diagonalization.
    """
    H = build_tfim_hamiltonian(N, J, h)
    eigenvalues = np.linalg.eigvalsh(H)
    return float(eigenvalues[0])


def build_tfim_pauli_list(N: int, J: float = 1.0, h: float = 1.0) -> List[Tuple[str, float]]:
    """
    Constructs the list of (Pauli_string, coefficient) for Qiskit SparsePauliOp.
    Note: Qiskit ordering is right-to-left (little-endian).
    """
    paulis = []

    # ZZ interactions: -J * Z_i Z_{i+1}
    for i in range(N - 1):
        s = ['I'] * N
        s[i] = 'Z'
        s[i + 1] = 'Z'
        # Reverse string for Qiskit endianness
        paulis.append((''.join(reversed(s)), -float(J)))

    # Transverse field: -h * X_i
    for i in range(N):
        s = ['I'] * N
        s[i] = 'X'
        paulis.append((''.join(reversed(s)), -float(h)))

    return paulis


def build_tfim_pauli_op(N: int, J: float = 1.0, h: float = 1.0) -> SparsePauliOp:
    """
    Returns SparsePauliOp representation of the TFIM Hamiltonian.
    """
    pauli_list = build_tfim_pauli_list(N, J, h)
    return SparsePauliOp.from_list(pauli_list)


def build_tfim_ansatz(N: int, reps: int = 2, entanglement: str = 'linear') -> QuantumCircuit:
    """
    Builds a hardware-efficient parameterized ansatz for VQE.
    """
    return efficient_su2(num_qubits=N, reps=reps, entanglement=entanglement)


def get_parity_operator(N: int) -> SparsePauliOp:
    """
    Returns the global Z2 parity symmetry operator P = prod_{i=0}^{N-1} X_i.
    Since [H, P] = 0, the ground state has defined parity.
    """
    return SparsePauliOp.from_list([('X' * N, 1.0)])


if __name__ == "__main__":
    N, J, h = 4, 1.0, 1.0
    e0 = exact_ground_energy(N, J, h)
    print(f"TFIM (N={N}, J={J}, h={h}) Exact Ground-State Energy: {e0:.6f}")
