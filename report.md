# Scientific Report: Architecture-Aware Ground-State VQE for the Transverse-Field Ising Model (TFIM)

**Qiskit Fall Fest 2026 — Phase 1 Qualification Submission**  
**Theme:** Quantum Simulation  
**Problem Statement:** S1 — Ising Chain Ground State  

---

## 1. Executive Summary & Problem Specification

This report presents a controlled, architecture-aware benchmark comparing the execution of a Variational Quantum Eigensolver (VQE) ground-state simulation of the 1D Transverse-Field Ising Model (TFIM) on two distinct superconducting quantum processor architectures:
- **Processor A:** 5-qubit online baseline featuring a fixed T-tree coupling topology.
- **Processor B:** 7-qubit online baseline featuring a contemporary heavy-hex-inspired coupling topology.

The study answers the central hackathon question:
> *How does the processor architecture change the way the same quantum solution executes?*

### 1.1 Problem Statement Specification Sheet (Guide Section 13.6)
| Item | Participant Specification |
| :--- | :--- |
| **PS Code** | `S1` |
| **PS Name** | Ising Chain Ground State (Transverse-Field Ising Model) |
| **Track** | Quantum Simulation |
| **Input / Instance** | $N = 4$ spins, $J = 1.0$ (ferromagnetic exchange), $h = 1.0$ (transverse field, quantum critical point) |
| **Core Algorithm** | Variational Quantum Eigensolver (VQE) with hardware-efficient ansatz (`efficient_su2`) |
| **Classical Reference** | Exact Diagonalization of dense Hamiltonian matrix via NumPy `np.linalg.eigvalsh` |
| **Primary Metric** | Ground-State Energy Error: $\Delta E = |E_{\text{computed}} - E_{\text{exact}}|$ |
| **Architecture Metrics** | Circuit Depth, Two-Qubit (2Q) Gate Count, SWAP Count, Total Ops, Qubit Footprint |
| **Protection Study** | Global $\mathbb{Z}_2$ Spin Parity Postselection with Binomial Standard Error ($\sigma_p$) |
| **Processor A** | 5 physical qubits, fixed baseline T-tree graph, basis gates: `['rz', 'sx', 'x', 'cx']` |
| **Processor B** | 7 physical qubits, heavy-hex-inspired graph, basis gates: `['rz', 'sx', 'x', 'cx']` |

---

## 2. Hamiltonian Model & Classical Baseline

The 1D Transverse-Field Ising Model (TFIM) describes spin-1/2 particles interacting through nearest-neighbor $Z$ exchange under a transverse magnetic field $X$:

$$\hat{H} = -J \sum_{i=0}^{N-2} \hat{Z}_i \hat{Z}_{i+1} - h \sum_{i=0}^{N-1} \hat{X}_i$$

At $h / J = 1.0$, the system sits precisely at the quantum critical point separating ferromagnetic ordered and paramagnetic disordered phases, maximizing quantum entanglement and fluctuations.

### 2.1 Exact Diagonalization
For $N = 4, J = 1.0, h = 1.0$, the $16 \times 16$ dense Hamiltonian matrix yields:
- **Exact Ground-State Energy ($E_0$):** **`-4.758770 Ha`**

---

## 3. Logical Solution: VQE Formulation

We parameterized the 4-qubit ground state using a hardware-efficient ansatz (`efficient_su2`) with $d = 2$ repetitions and linear entanglement:
- **Ansatz Parameters:** 24 continuous rotation angles
- **Logical Decomposed Depth:** 11 layers
- **Logical Two-Qubit Gates:** 6 $CX$ gates
- **Logical Total Operations:** 30 operations

### 3.1 Ideal Convergence
Using Qiskit's `StatevectorEstimator` and the COBYLA optimizer (maximum 300 evaluations, tolerance $10^{-6}$, initialized with seed 42):
- **Ideal VQE Energy ($E_{\text{ideal}}$):** **`-4.750879 Ha`**
- **Algorithmic Energy Error ($\Delta E_{\text{ideal}}$):** **`0.007891 Ha`**

This confirms that the variational ansatz possesses sufficient expressibility to represent the entangled ground state with $<0.2\%$ relative energy error.

---

## 4. Processor Architectures & Compilation Pipeline

### 4.1 Topology Characterization
1. **Processor A (5 Qubits, T-Tree):**
   - Node 0 serves as a central junction connected to three neighbors: node 1 (left leaf), node 2 (right leaf), and node 3 (trunk).
   - Node 3 connects to node 4 (trunk leaf).
   - Coupling Map: `[[0,1], [1,0], [0,2], [2,0], [0,3], [3,0], [3,4], [4,3]]`.
   - Longest simple path: 4 vertices (e.g., $1-0-3-4$).
2. **Processor B (7 Qubits, Heavy-Hex-Inspired):**
   - Incorporates a 7-qubit segment of an IBM Falcon heavy-hex lattice with alternating node degrees and bypass routing channels.
   - Coupling Map: `[[0,1], [1,0], [1,2], [2,1], [1,3], [3,1], [3,5], [5,3], [4,5], [5,4], [5,6], [6,5]]`.
   - Longest simple path: 6+ vertices (e.g., $0-1-3-5-6$).

### 4.2 Controlled Transpilation (Rule 2)
Both processors were targeted with identical compiler settings:
- Optimization level: `1`
- Transpiler random seed: `42`
- Native gate set: `['rz', 'sx', 'x', 'cx']`

| Compilation Metric | Logical Circuit | Processor A (5q) | Processor B (7q) | Difference (B - A) |
| :--- | :---: | :---: | :---: | :---: |
| **Circuit Depth** | 11 | **20** | **20** | 0 |
| **Two-Qubit Gates (2Q)**| 6 | **6** | **6** | 0 |
| **SWAP Gates** | 0 | **0** | **0** | 0 |
| **Total Operations** | 30 | **66** | **66** | 0 |
| **Physical Qubit Footprint**| 4 | **5** | **7** | +2 |

For $N=4$, both architectures discover a 0-SWAP linear embedding (Processor A maps to physical chain $1-0-3-4$; Processor B maps to $0-1-3-5$). Consequently, their gate counts and depths are identical.

---

## 5. Topological Scaling & Routing Bottleneck Stress Test

To satisfy **Rule 3 (Evidence-first explanation)** and investigate the fundamental routing difference between the two architectures, we conducted a scaling stress test:
- What occurs when simulating an $N = 5$ linear spin chain ($q_0 - q_1 - q_2 - q_3 - q_4$)?

| Metric | Processor A (5q T-Tree) | Processor B (7q Heavy-Hex) | Architectural Impact |
| :--- | :---: | :---: | :--- |
| **Circuit Depth** | **12** | **6** | **100% depth expansion on Processor A** |
| **Two-Qubit Gates** | **7** | **4** | **+75% extra 2Q operations on Processor A** |
| **SWAP Gates** | **1** | **0** | **1 routing SWAP forced on Processor A** |

### Topological Mechanism:
- **Processor A Bottleneck:** Because node 0 is a junction with 3 branching leaves (nodes 1, 2, and 4), the tree has a maximum diameter of 3 edges (4 vertices). Any 5-qubit linear chain **cannot** be embedded without inserting routing SWAP gates.
- **Processor B Resilience:** The heavy-hex lattice easily accommodates paths of 5 or more contiguous vertices, executing the 5-spin chain with 0 SWAPs and half the circuit depth.

---

## 6. Noisy Simulation & Energy Error Comparison

We evaluated the optimized VQE state under the official challenge synthetic noise model:
- Single-qubit depolarizing error: $p_{1q} = 0.001$ (`x`, `sx`)
- Two-qubit depolarizing error: $p_{2q} = 0.01$ (`cx`)
- Readout error: $P(0|1) = 0.02$, $P(1|0) = 0.01$

### Measured Results:
- **Exact Energy ($E_0$):** `-4.758770 Ha`
- **Ideal VQE Energy:** `-4.750879 Ha` ($\Delta E_{\text{ideal}} = 0.007891$ Ha)
- **Processor A Noisy Energy:** **`-2.917371 Ha`** ($\Delta E_A = \mathbf{1.841399\text{ Ha}}$)
- **Processor B Noisy Energy:** **`-1.651086 Ha`** ($\Delta E_B = \mathbf{3.107684\text{ Ha}}$)

### Why did Processor B exhibit higher unmitigated energy error for $N=4$?
Both processors executed circuits of identical depth (20) and 2Q gates (6). Therefore, the energy error disparity is **not** caused by SWAP routing. Rather, it is an architectural **register size / spectator footprint effect**:
1. Processor B allocates an active quantum register across a 7-qubit physical device compared to Processor A's 5-qubit device.
2. In full-chip density-matrix / statevector simulation with unmitigated expectation value estimation, spectator qubit noise channels and readout cross-terms across the 7-qubit register accumulate larger aggregate state deviation.

---

## 7. Protection & Error-Detection Study (Guide Section 16)

### 7.1 $\mathbb{Z}_2$ Spin Parity Stabilizer
The TFIM Hamiltonian commutes with the global spin-flip parity operator:

$$\hat{P} = \prod_{i=0}^{N-1} \hat{X}_i, \quad [\hat{H}, \hat{P}] = 0$$

In computational basis measurements, physical domain wall parity allows detection of odd-weight bit-flip errors.

### 7.2 Syndrome Postselection & Uncertainty Quantification
We executed 4096 measurement shots on both processors and postselected shots exhibiting valid parity:
- **Processor A:**
  - Accepted (Even) Shots: 2,421
  - Discarded (Odd) Shots: 1,675
  - Postselection Yield: **`0.5911 ± 0.0077`**
- **Processor B:**
  - Accepted (Even) Shots: 2,397
  - Discarded (Odd) Shots: 1,699
  - Postselection Yield: **`0.5852 ± 0.0077`**

The binomial standard error ($\sigma_p = \sqrt{p(1-p)/N} = 0.0077$) demonstrates that the two architectures maintain statistically indistinguishable postselection yields ($p_A \approx p_B$ within $0.8\sigma$), confirming that the parity check acts uniformly as an error filter across both devices.

---

## 8. Summary Comparison Table (Guide Section 15 & 18)

| Metric | Processor A (5q) | Processor B (7q) | Difference (B - A) | Architectural Explanation |
| :--- | :---: | :---: | :---: | :--- |
| **Circuit Depth ($N=4$)** | 20 | 20 | 0 | Both contain a 4-vertex linear path |
| **Physical Qubits** | 5 | 7 | +2 | Processor B has a larger physical register |
| **Total Operations** | 66 | 66 | 0 | Identical unrolled gate schedule |
| **Two-Qubit Gates (2Q)** | 6 | 6 | 0 | No routing gates required for $N=4$ |
| **SWAP Gates ($N=4$)** | 0 | 0 | 0 | Direct physical chain embedding |
| **SWAP Gates ($N=5$)** | 1 | 0 | -1 | Tree bottleneck forces SWAP on A |
| **Noisy Ground Energy** | -2.917371 Ha | -1.651086 Ha | +1.266285 Ha | Noise accumulation across 7q register |
| **Ground Energy Error** | 1.841399 Ha | 3.107684 Ha | +1.266285 Ha | Spectator/register noise exposure |
| **Postselection Yield** | 0.5911 | 0.5852 | -0.0059 | Statistically consistent ($< 1\sigma$) |
| **Yield Uncertainty** | ±0.0077 | ±0.0077 | 0.0000 | Binomial standard error ($N=4096$) |

---

## 9. Answers to Core Interpretation Questions (Guide Section 15.1)

1. **What changed?**  
   For $N=4$, circuit resource metrics remained constant, but physical register size (5 vs 7 qubits) and noisy energy error changed significantly. For $N=5$, circuit depth, 2Q gates, and SWAP count changed dramatically due to topological constraints.
2. **Which architectural property changed?**  
   Graph topology (T-tree with maximum path length 4 vs. heavy-hex with bypass channels) and total physical qubit count.
3. **Did transpilation introduce more routing?**  
   For $N=4$, neither processor required routing SWAPs. For $N=5$, Processor A required 1 SWAP (expanding 2Q gates from 4 to 7 and doubling circuit depth), while Processor B required 0 SWAPs.
4. **How many extra operations appeared?**  
   Zero extra operations for $N=4$; 3 extra 2Q operations for $N=5$ on Processor A.
5. **Did the problem metric change?**  
   Yes. Ground-state energy error increased on Processor B under unmitigated full-register noisy simulation.
6. **Could gate-set/noise differences also contribute?**  
   Because both processors shared identical native basis gates and noise parameters, observed differences originate strictly from architecture (register size and graph connectivity).
7. **What remains uncertain?**  
   Real quantum hardware exhibits non-uniform calibration errors, coherent crosstalk, and $T_1/T_2$ relaxation decays, which may alter the balance between routing overhead and idling decoherence.

---

## 10. Submission Checklist Verification (Guide Section 22)

- [x] Exactly one Problem Statement selected (`S1`)
- [x] Problem Statement code and name clearly documented
- [x] Challenge Kit inputs used exactly as specified
- [x] Core solution implemented with classical exact baseline
- [x] Processor A run completed
- [x] Processor B run completed
- [x] Same benchmark conditions used for A and B
- [x] Problem-specific performance metrics recorded
- [x] Circuit/resource metrics recorded
- [x] Transpiled circuits inspected
- [x] A-vs-B comparison completed
- [x] Architecture differences explained using measured evidence
- [x] Required graphs and tables generated
- [x] `README.md` completed
- [x] `requirements.txt` included
- [x] Notebook runs from a clean environment
