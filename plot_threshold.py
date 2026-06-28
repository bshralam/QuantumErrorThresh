"""
Run the threshold sweep and save a log-scale plot of logical error rate vs.
physical error rate, one curve per code distance. The crossing region is the
threshold: below it, higher-d curves sit lower (good); above it, they sit
higher (bad).

Colorblind-safe palette (Okabe-Ito) so the figure reads cleanly in print.
"""

import matplotlib.pyplot as plt
from surface_code import threshold_sweep

OKABE_ITO = ["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E69F00"]


def main():
    results = threshold_sweep(distances=(3, 5, 7), shots=20000)

    fig, ax = plt.subplots(figsize=(6.5, 5))
    for i, (d, row) in enumerate(sorted(results.items())):
        ps = [p for p, _ in row]
        lers = [l for _, l in row]
        ax.plot(ps, lers, "o-", color=OKABE_ITO[i % len(OKABE_ITO)],
                label=f"d = {d}", linewidth=1.8, markersize=5)

    ax.set_yscale("log")
    ax.set_xlabel("Physical error rate $p$")
    ax.set_ylabel("Logical error rate $p_L$")
    ax.set_title("Rotated surface code: threshold under circuit-level noise")
    ax.legend(title="Code distance")
    ax.grid(True, which="both", alpha=0.3)
    fig.tight_layout()
    fig.savefig("threshold.png", dpi=150)
    print("\nSaved threshold.png")


if __name__ == "__main__":
    main()
