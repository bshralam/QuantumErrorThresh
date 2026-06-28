"""
Surface-code memory experiment: simulation, decoding, and threshold extraction.

WHAT THIS DOES
--------------
Simulates a rotated surface code preserving a single logical qubit through
`rounds` of stabilizer measurement under circuit-level depolarizing noise,
decodes the measurement record with minimum-weight perfect matching (MWPM),
and measures the logical error rate as a function of physical error rate `p`
for several code distances. Where the curves cross is the threshold.

WHY EACH PIECE IS HERE (read before an interview)
-------------------------------------------------
- stim.Circuit.generated(...) builds the full syndrome-extraction circuit:
  data qubits, ancilla (measure) qubits, the CX schedule that maps each
  stabilizer onto its ancilla, and noise on every operation. We use
  'rotated_memory_z' = rotated surface code, Z-basis memory experiment
  (initialize |0>_L, idle through `rounds`, measure Z_L).

- detector_error_model(decompose_errors=True): converts the noisy circuit
  into a graph of DETECTORS (parity changes between consecutive stabilizer
  rounds) and the error mechanisms that flip them. decompose_errors splits
  correlated Y-type errors into X and Z components so the problem becomes a
  matching problem on two decoupled graphs -- this is exactly what makes
  MWPM applicable.

- pymatching.Matching: each detection event is a node; an error that flips
  two detectors is an edge. The decoder finds the minimum-weight set of
  edges (lowest-probability set of errors) consistent with the observed
  detections. If the inferred correction differs from the true error by a
  logical operator, that's a logical failure -- counted against `obs`.

THE THRESHOLD, IN ONE SENTENCE
------------------------------
Below threshold, adding distance suppresses logical error exponentially
(more redundancy wins); above threshold, more qubits means more error
mechanisms than the code can correct, so adding distance HURTS. The crossing
point is the threshold p_th (~0.5-1% for circuit-level noise on the surface code).
"""

import stim
import pymatching
import numpy as np


def build_circuit(distance: int, rounds: int, p: float) -> stim.Circuit:
    """Construct a noisy rotated-surface-code Z-memory circuit.

    All four noise channels are set to the same physical error rate `p` so the
    threshold sweep has a single knob. In a more careful study you would let
    these differ (e.g. measurement error vs. gate error).
    """
    return stim.Circuit.generated(
        "surface_code:rotated_memory_z",
        distance=distance,
        rounds=rounds,
        after_clifford_depolarization=p,        # 2-qubit gate noise
        after_reset_flip_probability=p,         # ancilla reset error
        before_measure_flip_probability=p,      # measurement error
        before_round_data_depolarization=p,     # data-qubit idling noise
    )


def logical_error_rate(distance: int, rounds: int, p: float, shots: int = 20000) -> float:
    """Return the fraction of shots where the decoder's correction left a
    logical error (i.e. predicted observable != true observable)."""
    circuit = build_circuit(distance, rounds, p)

    # Sampler over detectors (syndrome) and observables (true logical value).
    sampler = circuit.compile_detector_sampler()

    # Decoding graph derived from the noise model itself -- the decoder's edge
    # weights come from the actual error probabilities, not hand-tuning.
    dem = circuit.detector_error_model(decompose_errors=True)
    matching = pymatching.Matching.from_detector_error_model(dem)

    detection_events, observable_flips = sampler.sample(shots, separate_observables=True)
    predictions = matching.decode_batch(detection_events)

    num_errors = np.sum(predictions[:, 0] != observable_flips[:, 0])
    return num_errors / shots


def threshold_sweep(distances=(3, 5, 7),
                    physical_error_rates=None,
                    shots: int = 20000):
    """Sweep p across several distances. Returns {distance: [(p, ler), ...]}.

    Rounds is set equal to distance, the standard choice so the time direction
    of the decoding graph is balanced with the spatial code distance.
    """
    if physical_error_rates is None:
        physical_error_rates = np.linspace(0.002, 0.02, 8)

    results = {}
    for d in distances:
        row = []
        for p in physical_error_rates:
            ler = logical_error_rate(d, rounds=d, p=float(p), shots=shots)
            row.append((float(p), ler))
            print(f"d={d}  p={p:.4f}  ->  logical error rate {ler:.5f}")
        results[d] = row
    return results


if __name__ == "__main__":
    print("Surface-code threshold sweep (circuit-level depolarizing noise)\n")
    threshold_sweep()
