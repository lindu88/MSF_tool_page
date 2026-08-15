#!/usr/bin/env python3

"""Calendar heatmaps for strict 5-column search-results TSV files."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import calplot
import matplotlib.pyplot as plt

from .msf_plot_tools.common import (
    DEFAULT_NULL_COLOR,
    aggregate_daily_values,
    apply_colorbar_bound_tick_labels,
    apply_colorbar_data_bound_ticks,
    apply_hit_count_ticks,
    apply_weekday_layout,
    build_date_index,
    calendar_colormap_kwargs,
    ensure_output_dir,
    flatten_axes,
    load_null_periods_tsv,
    load_strict_search_results_tsv,
    normalize_site_filter,
    null_dates_from_periods,
    overlay_null_collection_periods,
    position_suptitle_close_to_calendar,
    resize_colorbar_to_calendar,
    safe_filename,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Plot one calendar heatmap per compound from a strict 5-column "
            "search-results TSV."
        )
    )
    parser.add_argument("input_tsv", help="Path to the strict search-results TSV.")
    parser.add_argument(
        "--site",
        default="AMB",
        help='Site filter such as "AMB". Use "ALL" to disable filtering.',
    )
    parser.add_argument(
        "--value-mode",
        choices=["presence", "hit_count", "max_value", "sum_value"],
        default="hit_count",
        help="Daily aggregation mode for each compound.",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=None,
        help="Plot only the top N compounds by frequency.",
    )
    parser.add_argument(
        "--colormap",
        default="plasma",
        help="Matplotlib colormap name for the calendar cells.",
    )
    parser.add_argument(
        "--null-periods",
        help="Optional 2-column TSV of null collection periods: start_date<TAB>end_date.",
    )
    parser.add_argument(
        "--null-color",
        default=DEFAULT_NULL_COLOR,
        help="Color used to show null collection periods outside the main colormap.",
    )
    parser.add_argument(
        "--monday-at-bottom",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Flip the weekday order so Monday is at the bottom.",
    )
    parser.add_argument(
        "--days-on-left",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Place weekday labels on the left side of the plot.",
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


def main(argv: list[str] | None = None) -> list[Any]:
    figs = []

    args = build_parser().parse_args(argv)

    if args.no_show and not args.save_dir:
        raise ValueError("--no-show requires --save-dir so the plots go somewhere.")

    df = load_strict_search_results_tsv(args.input_tsv)
    site_filter = normalize_site_filter(args.site)
    if site_filter is not None:
        df = df[df["site"] == site_filter]
    if df.empty:
        raise ValueError("No rows remain after applying the site filter.")

    null_periods = load_null_periods_tsv(args.null_periods)
    null_dates = null_dates_from_periods(null_periods)

    if args.top_n is not None:
        top_names = df["plot_name"].value_counts().head(args.top_n).index.tolist()
        df = df[df["plot_name"].isin(top_names)]
    else:
        top_names = sorted(df["plot_name"].unique())

    date_index = build_date_index(df["date"], null_dates)
    plot_years = sorted(date_index.year.unique())
    output_dir = ensure_output_dir(args.save_dir)

    for plot_name in top_names:
        subset = df[df["plot_name"] == plot_name]
        series = aggregate_daily_values(
            subset,
            date_index=date_index,
            value_mode=args.value_mode,
            value_column="integrated_signal",
        )
        plot_kwargs = calendar_colormap_kwargs(
            series=series,
            value_mode=args.value_mode,
            colormap_name=args.colormap,
        )

        fig, ax = calplot.calplot(
            series,
            suptitle=plot_name,
            figsize=(12, 3.2),
            colorbar=(args.value_mode != "presence"),
            **plot_kwargs,
        )
        year_axes = flatten_axes(ax)

        position_suptitle_close_to_calendar(fig, year_axes)
        overlay_null_collection_periods(
            year_axes=year_axes,
            plot_years=plot_years,
            null_dates=null_dates,
            null_color=args.null_color,
        )
        apply_weekday_layout(
            year_axes,
            monday_at_bottom=args.monday_at_bottom,
            days_on_left=args.days_on_left,
        )

        if args.value_mode != "presence":
            colorbar_ax = resize_colorbar_to_calendar(fig, year_axes)
            if args.value_mode == "hit_count":
                apply_hit_count_ticks(colorbar_ax, series)
            else:
                apply_colorbar_data_bound_ticks(colorbar_ax, series)
                apply_colorbar_bound_tick_labels(
                    colorbar_ax,
                    series,
                    round_bounds_to_int=True,
                )

        figs.append(fig)

        if output_dir is not None:
            output_path = output_dir / f"{safe_filename(plot_name)}_{args.value_mode}.png"
            fig.savefig(output_path, dpi=args.dpi, bbox_inches="tight")

        if args.no_show:
            plt.close(fig)
        else:
            plt.show()
            plt.close(fig)

    return figs


if __name__ == "__main__":
    raise SystemExit(main())
