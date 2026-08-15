#!/usr/bin/env python3

"""Hourly bar plots for strict 5-column search-results TSV files."""

from __future__ import annotations

import argparse
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd

from .msf_plot_tools.common import (
    ensure_output_dir,
    format_title_suffix,
    load_strict_search_results_tsv,
    normalize_site_filter,
    safe_filename,
    sample_colormap_color,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Plot hourly summaries from a strict 5-column search-results TSV."
    )
    parser.add_argument("input_tsv", help="Path to the strict search-results TSV.")
    parser.add_argument(
        "--site",
        default="AMB",
        help='Site filter such as "AMB". Use "ALL" to disable filtering.',
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=None,
        help="Plot only the top N compounds by frequency.",
    )
    parser.add_argument(
        "--hour-mode",
        choices=["detections", "sum_value", "mean_value"],
        default="detections",
        help="Hourly aggregation mode.",
    )
    parser.add_argument(
        "--normalize-by-sample-count",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Normalize detections and sums by the number of unique samples per hour.",
    )
    parser.add_argument(
        "--title-suffix",
        help="Optional text appended to the subtitle, for example '2025'.",
    )
    parser.add_argument(
        "--bar-color",
        help="Optional Matplotlib color for the bars. Defaults to a dark plasma tone.",
    )
    parser.add_argument(
        "--save-dir",
        help="Optional directory for exported PNGs. One file is written per compound.",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=200,
        help="DPI to use when saving PNG files.",
    )
    parser.add_argument(
        "--no-show",
        action="store_true",
        help="Do not display figures interactively.",
    )
    return parser


def finish_hour_plot(
    fig,
    compound: str,
    ylabel: str,
    subtitle: str,
    hours,
    hour_labels,
    *,
    output_path=None,
    dpi: int,
    show_plot: bool,
):
    plt.xticks(hours, hour_labels, rotation=45, ha="right")
    plt.xlabel("Time of day")
    plt.ylabel(ylabel)
    plt.title(f"{compound}\n{subtitle}")
    plt.tight_layout()

    if output_path is not None:
        fig.savefig(output_path, dpi=dpi, bbox_inches="tight")

    if show_plot:
        plt.show()
        plt.close(fig)
    else:
        plt.close(fig)

    return fig


def main(argv: list[str] | None = None) -> list[Any]:
    args = build_parser().parse_args(argv)

    figs = []

    if args.no_show and not args.save_dir:
        raise ValueError("--no-show requires --save-dir so the plots go somewhere.")

    df = load_strict_search_results_tsv(args.input_tsv)
    site_filter = normalize_site_filter(args.site)
    if site_filter is not None:
        df = df[df["site"] == site_filter]
    if df.empty:
        raise ValueError("No rows remain after applying the site filter.")

    if args.top_n is not None:
        top_compounds = df["plot_name"].value_counts().head(args.top_n).index.tolist()
        df = df[df["plot_name"].isin(top_compounds)]
    else:
        top_compounds = sorted(df["plot_name"].unique())

    hours = list(range(24))
    hour_labels = [f"{hour:02d}:00" for hour in hours]
    sample_counts_by_hour = (
        df.groupby("hour")["sample_name"].nunique().reindex(hours, fill_value=0).astype(float)
    )
    sample_counts_nonzero = sample_counts_by_hour.replace(0, pd.NA)
    detection_suffix = format_title_suffix(args.title_suffix)
    metric_context = (
        f"integrated signal; {args.title_suffix.strip()}"
        if args.title_suffix and args.title_suffix.strip()
        else "integrated signal"
    )
    bar_color = args.bar_color or sample_colormap_color("plasma", 0.15)
    output_dir = ensure_output_dir(args.save_dir)

    for compound in top_compounds:
        subset = df[df["plot_name"] == compound].copy()

        if args.hour_mode == "detections":
            values = subset.groupby("hour").size().reindex(hours, fill_value=0).astype(float)
            if args.normalize_by_sample_count:
                values = values.divide(sample_counts_nonzero).fillna(0.0)
                ylabel = "Detections per sample"
                subtitle = f"Hourly detections / sample{detection_suffix}"
            else:
                ylabel = "Number of detections"
                subtitle = f"Hourly detections{detection_suffix}"
        elif args.hour_mode == "sum_value":
            values = (
                subset.groupby("hour")["integrated_signal"]
                .sum()
                .reindex(hours, fill_value=0)
                .astype(float)
            )
            if args.normalize_by_sample_count:
                values = values.divide(sample_counts_nonzero).fillna(0.0)
                ylabel = "Sum integrated signal per sample"
                subtitle = f"Hourly sum / sample ({metric_context})"
            else:
                ylabel = "Sum integrated signal"
                subtitle = f"Hourly sum ({metric_context})"
        else:
            values = (
                subset.groupby("hour")["integrated_signal"]
                .mean()
                .reindex(hours, fill_value=0)
                .astype(float)
            )
            ylabel = "Mean integrated signal"
            subtitle = f"Hourly mean ({metric_context})"

        fig = plt.figure(figsize=(10, 4.5))
        plt.bar(hours, values.values, color=bar_color)

        output_path = None
        if output_dir is not None:
            output_path = output_dir / f"{safe_filename(compound)}_{args.hour_mode}.png"

        fig = finish_hour_plot(
            fig,
            compound=compound,
            ylabel=ylabel,
            subtitle=subtitle,
            hours=hours,
            hour_labels=hour_labels,
            output_path=output_path,
            dpi=args.dpi,
            show_plot=not args.no_show,
        )
        figs.append(fig)

    return figs


if __name__ == "__main__":
    raise SystemExit(main())
