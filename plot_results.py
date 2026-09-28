#!/usr/bin/env python3
import argparse

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import t


def compute_stats(df, traffic_type):
    subset = df[df["traffic_type"] == traffic_type]
    intensities = sorted(subset["intensity"].unique())
    means = []
    ci_half_widths = []

    for intensity in intensities:
        values = np.array(subset[subset["intensity"] == intensity]["mean_completion_time"])
        n = len(values)
        mean_fct = np.mean(values)
        s = np.std(values, ddof=1)
        se = s / np.sqrt(n)
        t_crit = t.ppf(0.975, df=n - 1)
        means.append(mean_fct)
        ci_half_widths.append(t_crit * se)

    return intensities, means, ci_half_widths


def plot_results(csv_path, output_path, title):
    df = pd.read_csv(csv_path)
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.5))

    for traffic_type, label, ax in [(1, "Web Search", axes[0]), (2, "Data Mining", axes[1])]:
        intensities, means, ci_half_widths = compute_stats(df, traffic_type)
        ax.bar(intensities, means, yerr=ci_half_widths, capsize=4,
               color="#4C72B0", edgecolor="black", width=0.6, zorder=2)
        ax.set_title(label, fontweight="bold")
        ax.set_xlabel("Traffic Intensity (flows/s)", fontweight="bold")
        ax.set_ylabel("Flow Completion Time (s)", fontweight="bold")
        ax.set_xticks(intensities)
        ax.grid(axis="y", alpha=0.3, zorder=0)

    if title:
        fig.suptitle(title, fontweight="bold")

    fig.tight_layout()
    fig.savefig(output_path or csv_path.rsplit(".", 1)[0] + ".png", dpi=200, bbox_inches="tight")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_file")
    parser.add_argument("--output", "-o")
    parser.add_argument("--title", "-t")
    args = parser.parse_args()
    plot_results(args.csv_file, args.output, args.title)
