# solution_tfim_simulation/run_processor_B.py
"""
Standalone execution script for Processor B (7-Qubit Heavy-Hex-Inspired Baseline).
Performs TFIM ground-state VQE transpilation, noisy simulation, and parity postselection.
"""

import sys
from pathlib import Path

# Ensure package imports work regardless of execution directory
current_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(current_dir))

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from qiskit import transpile
from qiskit.primitives import StatevectorEstimator
from qiskit.quantum_info import SparsePauliOp
from qiskit_aer import AerSimulator
from qiskit_aer.primitives import EstimatorV2 as AerEstimator

from src.problem import exact_ground_energy, build_tfim_pauli_op, build_tfim_ansatz
from src.processor_b import ProcessorB
from src.metrics import circuit_metrics, proportion_standard_error, energy_error
from src.visualization import draw_processor_graph


def run_processor_b():
    print("=" * 60)
    print("Executing Dedicated Benchmark on Processor B (7 Qubits, Heavy-Hex)")
    print("=" * 60)

    # 1. Initialize Problem
    N, J, h = 4, 1.0, 1.0
    E_exact = exact_ground_energy(N, J, h)
    hamiltonian = build_tfim_pauli_op(N, J, h)
    print(f"Problem: TFIM Chain (N={N}, J={J}, h={h})")
    print(f"Classical Exact Ground Energy: {E_exact:.6f} Ha")

    # 2. Optimize Ideal VQE State
    ansatz = build_tfim_ansatz(N, reps=2, entanglement="linear")
    ideal_estimator = StatevectorEstimator()

    def cost_func(params):
        job = ideal_estimator.run([(ansatz, hamiltonian, params)])
        return float(job.result()[0].data.evs)

    np.random.seed(42)
    x0 = np.random.uniform(-0.1, 0.1, ansatz.num_parameters)
    opt_res = minimize(cost_func, x0, method="COBYLA", options={"maxiter": 300, "tol": 1e-6})
    optimal_params = opt_res.x
    E_ideal = float(opt_res.fun)
    print(f"Ideal VQE Energy: {E_ideal:.6f} Ha (Error: {energy_error(E_ideal, E_exact):.6f} Ha)")

    # 3. Load Processor B
    proc_B = ProcessorB()
    print(f"\nLoaded: {proc_B.name} ({proc_B.num_qubits} qubits, {len(proc_B.coupling_map)} directed edges)")

    # Save Graph Image
    fig_path = current_dir / "results" / "figures" / "processor_B_graph.png"
    draw_processor_graph(proc_B.config, "Processor B: 7-Qubit Heavy-Hex-Inspired", str(fig_path), pos=proc_B.layout_pos)

    # 4. Transpile for Processor B
    compiled_B = transpile(
        ansatz,
        coupling_map=proc_B.get_coupling_map(),
        basis_gates=proc_B.basis_gates,
        optimization_level=1,
        seed_transpiler=42
    )
    metrics_B = circuit_metrics(compiled_B)
    print("\n--- Processor B Compilation Metrics ---")
    print(f"  Circuit Depth        : {metrics_B['depth']}")
    print(f"  Two-Qubit Gates (2Q) : {metrics_B['two_qubit_ops_estimate']}")
    print(f"  SWAP Gates           : {metrics_B['swap_count']}")
    print(f"  Total Operations     : {metrics_B['total_ops']}")
    print(f"  Physical Qubits Used : {metrics_B['num_qubits']}")

    # 5. Noisy Expectation Value Simulation
    noise_model = proc_B.get_noise_model()
    noisy_estimator = AerEstimator(options={"backend_options": {"noise_model": noise_model}})

    # Pad Hamiltonian for 7-qubit register
    pad = "I" * (proc_B.num_qubits - N)
    ext_hamiltonian = SparsePauliOp.from_list([
        (p + pad, c) for p, c in zip(hamiltonian.paulis.to_labels(), hamiltonian.coeffs)
    ])
    job = noisy_estimator.run([(compiled_B, ext_hamiltonian, optimal_params)])
    E_noisy_B = float(np.asarray(job.result()[0].data.evs).item())
    err_B = energy_error(E_noisy_B, E_exact)

    print("\n--- Processor B Noisy Evaluation ---")
    print(f"  Noisy Ground Energy  : {E_noisy_B:.6f} Ha")
    print(f"  Energy Error |E-E0|  : {err_B:.6f} Ha")

    # 6. Z2 Parity Postselection (4096 shots)
    shots = 4096
    qc_meas = compiled_B.copy()
    qc_meas.measure_all()
    bound = qc_meas.assign_parameters(optimal_params, inplace=False)
    sim = AerSimulator(noise_model=noise_model, seed_simulator=42)
    counts = sim.run(bound, shots=shots).result().get_counts()

    even, odd = 0, 0
    for bstring, c in counts.items():
        clean_b = bstring.replace(" ", "")
        if clean_b.count("1") % 2 == 0:
            even += c
        else:
            odd += c
    total = even + odd
    p_yield = even / total if total > 0 else 0.0
    se_yield = proportion_standard_error(p_yield, total)

    print("\n--- Processor B Parity Postselection ---")
    print(f"  Accepted (Even)      : {even}")
    print(f"  Discarded (Odd)      : {odd}")
    print(f"  Postselection Yield  : {p_yield:.4f} ± {se_yield:.4f}")

    # 7. Save Metrics Table
    results_df = pd.DataFrame([{
        "Processor": proc_B.name,
        "Num_Qubits": proc_B.num_qubits,
        "Depth": metrics_B["depth"],
        "Two_Q_Gates": metrics_B["two_qubit_ops_estimate"],
        "SWAPs": metrics_B["swap_count"],
        "Total_Ops": metrics_B["total_ops"],
        "Exact_Energy": E_exact,
        "Noisy_Energy": E_noisy_B,
        "Energy_Error": err_B,
        "Postselection_Yield": p_yield,
        "Yield_Uncertainty": se_yield
    }])
    table_path = current_dir / "results" / "tables" / "processor_B_metrics.csv"
    results_df.to_csv(table_path, index=False)
    print(f"\nSaved metrics to: {table_path}")
    print("=" * 60)


if __name__ == "__main__":
    run_processor_b()
