# solution_tfim_simulation/run_experiments.py
"""
End-to-end experiment pipeline for Phase 1 TFIM Ground State A/B Benchmarking.
Executes ideal VQE, transpilation for Processor A and B, noisy evaluation,
Z2 parity postselection, and generates all result tables and figures.
"""

import sys
from pathlib import Path

# Add solution directory to path
sys.path.insert(0, str(Path(__file__).parent))

import json
import math
import numpy as np
import pandas as pd
from scipy.optimize import minimize

from qiskit import QuantumCircuit
from qiskit.primitives import StatevectorEstimator
from qiskit.quantum_info import SparsePauliOp
from qiskit_aer import AerSimulator
from qiskit_aer.primitives import EstimatorV2 as AerEstimator

from src.problem import (
    exact_ground_energy,
    build_tfim_pauli_op,
    build_tfim_ansatz,
    get_parity_operator
)
from src.processors import (
    load_processor,
    build_noise_model
)
from src.routing import (
    transpile_for_processor,
    analyze_routing_overhead
)
from src.metrics import (
    circuit_metrics,
    proportion_standard_error,
    energy_error
)
from src.visualization import (
    draw_processor_graph,
    plot_ab_comparison,
    plot_logical_vs_transpiled,
    plot_architecture_tradeoffs
)


def run_all():
    print("=" * 60)
    print("Running Phase 1 TFIM Ground State A/B Experiment Suite")
    print("=" * 60)

    # 1. Setup problem instance
    N = 4
    J = 1.0
    h = 1.0
    print(f"Problem: Transverse-Field Ising Model (TFIM) Chain (N={N}, J={J}, h={h})")

    E_exact = exact_ground_energy(N, J, h)
    hamiltonian = build_tfim_pauli_op(N, J, h)
    parity_op = get_parity_operator(N)
    print(f"Classical Exact Baseline (Ground Energy): {E_exact:.6f} Ha")

    # Save raw problem data
    raw_data = {
        "problem_statement": "S1 - Ising Chain Ground State",
        "theme": "Quantum Simulation",
        "N": N,
        "J": J,
        "h": h,
        "exact_ground_energy": E_exact,
        "hamiltonian_paulis": [str(p) for p in hamiltonian.paulis.to_labels()],
        "hamiltonian_coeffs": [float(c.real) for c in hamiltonian.coeffs]
    }
    with open("solution_tfim_simulation/data/raw/problem_instance.json", "w") as f:
        json.dump(raw_data, f, indent=2)

    # 2. Ideal VQE Optimization
    print("\n[Step 2] Optimizing VQE on Ideal Statevector Estimator...")
    ansatz = build_tfim_ansatz(N, reps=2, entanglement='linear')
    num_params = ansatz.num_parameters
    logical_metrics = circuit_metrics(ansatz.decompose())

    ideal_estimator = StatevectorEstimator()

    def cost_func(params):
        job = ideal_estimator.run([(ansatz, hamiltonian, params)])
        return float(job.result()[0].data.evs)

    np.random.seed(42)
    init_params = np.random.uniform(-0.1, 0.1, num_params)

    opt_result = minimize(
        cost_func,
        init_params,
        method="COBYLA",
        options={"maxiter": 300, "tol": 1e-6}
    )

    optimal_params = opt_result.x
    E_vqe_ideal = float(opt_result.fun)
    err_ideal = energy_error(E_vqe_ideal, E_exact)

    print(f"Ideal VQE Energy  : {E_vqe_ideal:.6f} Ha")
    print(f"Ideal Energy Error: {err_ideal:.6f} Ha (Converged in {opt_result.nfev} evaluations)")

    # 3. Load Processors
    print("\n[Step 3] Loading Processor A and B Architectures...")
    proc_A = load_processor("solution_tfim_simulation/processors/processor_A.json")
    proc_B = load_processor("solution_tfim_simulation/processors/processor_B.json")

    print(f"Processor A: {proc_A['name']} ({proc_A['num_qubits']} qubits, {len(proc_A['coupling_map'])} directed edges)")
    print(f"Processor B: {proc_B['name']} ({proc_B['num_qubits']} qubits, {len(proc_B['coupling_map'])} directed edges)")

    # Draw processor graphs
    # Custom layout positions for visual fidelity to challenge slide
    pos_A = {
        0: (0.0, 1.0),   # Top junction
        1: (-0.6, 0.4),  # Left branch
        2: (0.6, 0.4),   # Right branch
        3: (0.0, 0.1),   # Trunk middle
        4: (0.0, -0.6)   # Trunk bottom
    }
    pos_B = {
        0: (-0.8, 0.8),
        1: (-0.2, 0.8),
        2: (0.4, 0.8),
        3: (-0.2, 0.1),
        4: (0.4, 0.1),
        5: (0.4, -0.6),
        6: (1.0, -0.6)
    }

    draw_processor_graph(proc_A, "Processor A: 5-Qubit Fixed Baseline Graph", "solution_tfim_simulation/results/figures/processor_A_graph.png", pos=pos_A)
    draw_processor_graph(proc_B, "Processor B: 7-Qubit Heavy-Hex-Inspired Graph", "solution_tfim_simulation/results/figures/processor_B_graph.png", pos=pos_B)
    print("Generated processor graph visualizations.")

    # 4. Transpile Circuit for Processor A and Processor B
    print("\n[Step 4] Controlled Transpilation (opt_level=1, seed=42)...")
    compiled_A = transpile_for_processor(ansatz, proc_A, optimization_level=1, seed_transpiler=42)
    compiled_B = transpile_for_processor(ansatz, proc_B, optimization_level=1, seed_transpiler=42)

    metrics_A = circuit_metrics(compiled_A)
    metrics_B = circuit_metrics(compiled_B)

    overhead_A = analyze_routing_overhead(ansatz.decompose(), compiled_A)
    overhead_B = analyze_routing_overhead(ansatz.decompose(), compiled_B)

    # Save per-processor metrics
    df_metrics_A = pd.DataFrame([metrics_A])
    df_metrics_B = pd.DataFrame([metrics_B])
    df_metrics_A.to_csv("solution_tfim_simulation/results/tables/processor_A_metrics.csv", index=False)
    df_metrics_B.to_csv("solution_tfim_simulation/results/tables/processor_B_metrics.csv", index=False)

    print(f"Processor A Transpiled: Depth={metrics_A['depth']}, 2Q Gates={metrics_A['two_qubit_ops_estimate']}, SWAPs={metrics_A['swap_count']}, Total Ops={metrics_A['total_ops']}")
    print(f"Processor B Transpiled: Depth={metrics_B['depth']}, 2Q Gates={metrics_B['two_qubit_ops_estimate']}, SWAPs={metrics_B['swap_count']}, Total Ops={metrics_B['total_ops']}")

    # 5. Build Noise Model & Evaluate Noisy Expectation Values
    print("\n[Step 5] Evaluating Noisy VQE on AerSimulator with Challenge Noise...")
    noise_model = build_noise_model()
    noisy_estimator = AerEstimator(
        options={"backend_options": {"noise_model": noise_model}}
    )

    def eval_noisy_energy(compiled_circ, params):
        n_circ = compiled_circ.num_qubits
        n_ham = hamiltonian.num_qubits

        # Pad Pauli terms with identity on unused physical qubits
        if n_circ > n_ham:
            pad = "I" * (n_circ - n_ham)
            ext_hamiltonian = SparsePauliOp.from_list([
                (p + pad, c) for p, c in zip(hamiltonian.paulis.to_labels(), hamiltonian.coeffs)
            ])
        else:
            ext_hamiltonian = hamiltonian

        job = noisy_estimator.run([(compiled_circ, ext_hamiltonian, params)])
        return float(np.asarray(job.result()[0].data.evs).item())

    E_noisy_A = eval_noisy_energy(compiled_A, optimal_params)
    E_noisy_B = eval_noisy_energy(compiled_B, optimal_params)

    err_noisy_A = energy_error(E_noisy_A, E_exact)
    err_noisy_B = energy_error(E_noisy_B, E_exact)

    print(f"Processor A Noisy Energy: {E_noisy_A:.6f} Ha (Error: {err_noisy_A:.6f} Ha)")
    print(f"Processor B Noisy Energy: {E_noisy_B:.6f} Ha (Error: {err_noisy_B:.6f} Ha)")

    # 6. Z2 Parity Error Detection & Postselection
    print("\n[Step 6] Syndrome Postselection via Z2 Parity Checks (4096 shots)...")
    shots = 4096
    seed = 42

    def run_postselection(compiled_circ, params):
        qc = compiled_circ.copy()
        qc.measure_all()
        bound = qc.assign_parameters(params, inplace=False)
        sim = AerSimulator(noise_model=noise_model, seed_simulator=seed)
        counts = sim.run(bound, shots=shots).result().get_counts()

        even, odd = 0, 0
        for bstring, cnt in counts.items():
            clean_b = bstring.replace(" ", "")
            # Check parity of computational basis state
            if clean_b.count("1") % 2 == 0:
                even += cnt
            else:
                odd += cnt
        total = even + odd
        yld = even / total if total > 0 else 0.0
        se_yld = proportion_standard_error(yld, total)
        return {
            "even": even,
            "odd": odd,
            "total": total,
            "yield": yld,
            "yield_se": se_yld,
            "counts": counts
        }

    ps_A = run_postselection(compiled_A, optimal_params)
    ps_B = run_postselection(compiled_B, optimal_params)

    print(f"Processor A Postselection Yield: {ps_A['yield']:.4f} ± {ps_A['yield_se']:.4f} (Even: {ps_A['even']}, Odd: {ps_A['odd']})")
    print(f"Processor B Postselection Yield: {ps_B['yield']:.4f} ± {ps_B['yield_se']:.4f} (Even: {ps_B['even']}, Odd: {ps_B['odd']})")

    # 7. Construct Comparison DataFrames and Export Tables
    print("\n[Step 7] Generating Comparison Tables...")
    table_ab = pd.DataFrame({
        "Metric": [
            "Circuit Depth",
            "Physical Qubits",
            "Total Operations",
            "Two-Qubit Gates (2Q)",
            "SWAP Gates",
            "Noisy Ground Energy (Ha)",
            "Energy Error |E_noisy - E_exact| (Ha)",
            "Postselection Yield",
            "Yield Std Error (±σ)"
        ],
        "Processor A": [
            metrics_A["depth"],
            metrics_A["num_qubits"],
            metrics_A["total_ops"],
            metrics_A["two_qubit_ops_estimate"],
            metrics_A["swap_count"],
            round(E_noisy_A, 6),
            round(err_noisy_A, 6),
            round(ps_A["yield"], 4),
            round(ps_A["yield_se"], 4)
        ],
        "Processor B": [
            metrics_B["depth"],
            metrics_B["num_qubits"],
            metrics_B["total_ops"],
            metrics_B["two_qubit_ops_estimate"],
            metrics_B["swap_count"],
            round(E_noisy_B, 6),
            round(err_noisy_B, 6),
            round(ps_B["yield"], 4),
            round(ps_B["yield_se"], 4)
        ]
    })
    table_ab["Difference (B - A)"] = [
        metrics_B["depth"] - metrics_A["depth"],
        metrics_B["num_qubits"] - metrics_A["num_qubits"],
        metrics_B["total_ops"] - metrics_A["total_ops"],
        metrics_B["two_qubit_ops_estimate"] - metrics_A["two_qubit_ops_estimate"],
        metrics_B["swap_count"] - metrics_A["swap_count"],
        round(E_noisy_B - E_noisy_A, 6),
        round(err_noisy_B - err_noisy_A, 6),
        round(ps_B["yield"] - ps_A["yield"], 4),
        round(ps_B["yield_se"] - ps_A["yield_se"], 4)
    ]
    table_ab.to_csv("solution_tfim_simulation/results/tables/AB_comparison.csv", index=False)

    final_summary = pd.DataFrame({
        "Metric": [
            "Problem Statement",
            "System Size (N spins)",
            "Exact Ground Energy (Ha)",
            "Ideal VQE Energy (Ha)",
            "Ideal VQE Error (Ha)",
            "Processor A Noisy Energy (Ha)",
            "Processor A Energy Error (Ha)",
            "Processor B Noisy Energy (Ha)",
            "Processor B Energy Error (Ha)",
            "Processor A Depth",
            "Processor B Depth",
            "Processor A 2Q Gates",
            "Processor B 2Q Gates",
            "Processor A Postselection Yield",
            "Processor B Postselection Yield"
        ],
        "Value": [
            "S1 - Ising Chain Ground State",
            N,
            round(E_exact, 6),
            round(E_vqe_ideal, 6),
            round(err_ideal, 6),
            round(E_noisy_A, 6),
            round(err_noisy_A, 6),
            round(E_noisy_B, 6),
            round(err_noisy_B, 6),
            metrics_A["depth"],
            metrics_B["depth"],
            metrics_A["two_qubit_ops_estimate"],
            metrics_B["two_qubit_ops_estimate"],
            f"{ps_A['yield']:.4f} ± {ps_A['yield_se']:.4f}",
            f"{ps_B['yield']:.4f} ± {ps_B['yield_se']:.4f}"
        ]
    })
    final_summary.to_csv("solution_tfim_simulation/results/tables/final_comparison.csv", index=False)

    # 8. Generate Result Figures
    print("\n[Step 8] Generating Comparative Figures...")
    df_bar = pd.DataFrame({
        "Processor A": [metrics_A["depth"], metrics_A["total_ops"], metrics_A["two_qubit_ops_estimate"], metrics_A["swap_count"]],
        "Processor B": [metrics_B["depth"], metrics_B["total_ops"], metrics_B["two_qubit_ops_estimate"], metrics_B["swap_count"]]
    }, index=["Depth", "Total Ops", "2Q Gates", "SWAPs"])
    plot_ab_comparison(df_bar, "solution_tfim_simulation/results/figures/AB_performance.png")

    plot_logical_vs_transpiled(
        logical_metrics,
        metrics_A,
        metrics_B,
        "solution_tfim_simulation/results/figures/logical_vs_transpiled.png"
    )

    tradeoff_df = pd.DataFrame([
        {
            "Processor": "Processor A (5q)",
            "Depth": metrics_A["depth"],
            "2Q Gates": metrics_A["two_qubit_ops_estimate"],
            "SWAPs": metrics_A["swap_count"],
            "Energy Error": err_noisy_A
        },
        {
            "Processor": "Processor B (7q)",
            "Depth": metrics_B["depth"],
            "2Q Gates": metrics_B["two_qubit_ops_estimate"],
            "SWAPs": metrics_B["swap_count"],
            "Energy Error": err_noisy_B
        }
    ])
    plot_architecture_tradeoffs(tradeoff_df, "solution_tfim_simulation/results/figures/architecture_tradeoffs.png")

    # Save processed results JSON
    processed_data = {
        "optimal_params": list(optimal_params),
        "circuit_metrics_A": metrics_A,
        "circuit_metrics_B": metrics_B,
        "postselection_A": {"even": ps_A["even"], "odd": ps_A["odd"], "yield": ps_A["yield"], "yield_se": ps_A["yield_se"]},
        "postselection_B": {"even": ps_B["even"], "odd": ps_B["odd"], "yield": ps_B["yield"], "yield_se": ps_B["yield_se"]}
    }
    with open("solution_tfim_simulation/data/processed/simulation_results.json", "w") as f:
        json.dump(processed_data, f, indent=2)

    print("\n" + "=" * 60)
    print("Experiment Suite Completed Successfully!")
    print("Tables saved to: solution_tfim_simulation/results/tables/")
    print("Figures saved to: solution_tfim_simulation/results/figures/")
    print("=" * 60)


if __name__ == "__main__":
    run_all()
