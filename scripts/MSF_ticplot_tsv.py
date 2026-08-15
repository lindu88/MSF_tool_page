#!/usr/bin/env python3

"""Calendar plot for strict 2-column TIC benzene-equivalent TSV files."""

from __future__ import annotations

import argparse
from pathlib import Path

import calplot
import matplotlib.pyplot as plt

from .msf_plot_tools.common import (
    DEFAULT_NULL_COLOR,
    aggregate_daily_values,
    apply_colorbar_data_bound_ticks,
    apply_colorbar_bound_tick_labels,
    apply_hit_count_ticks,
    apply_weekday_layout,
    build_date_index,
    calendar_colormap_kwargs,
    default_title_from_path,
    flatten_axes,
    load_null_periods_tsv,
    load_strict_tic_summary_tsv,
    null_dates_from_periods,
    overlay_null_collection_periods,
    position_suptitle_close_to_calendar,
    resize_colorbar_to_calendar,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Plot a calendar heatmap from a strict 2-column TIC summary TSV."
    )
    parser.add_argument("input_tsv", help="Path to the strict TIC summary TSV.")
    parser.add_argument(
        "--value-mode",
        choices=["presence", "hit_count", "max_value", "sum_value"],
        default="max_value",
        help="Daily aggregation mode for the benzene-equivalent values.",
    )
    parser.add_argument(
        "--title",
        help="Optional plot title. Defaults to a cleaned version of the input filename.",
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
        "--output",
        help="Optional output PNG path.",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=200,
        help="DPI to use when saving a PNG file.",
    )
    parser.add_argument(
        "--no-show",
        action="store_true",
        help="Do not display the figure interactively.",
    )
    return parser


def main(argv: list[str] | None = None) -> plt.Figure:
    args = build_parser().parse_args(argv)

    if args.no_show and not args.output:
        raise ValueError("--no-show requires --output so the plot is not discarded.")

    df = load_strict_tic_summary_tsv(args.input_tsv)
    null_periods = load_null_periods_tsv(args.null_periods)
    null_dates = null_dates_from_periods(null_periods)
    date_index = build_date_index(df["date"], null_dates)
    series = aggregate_daily_values(
        df,
        date_index=date_index,
        value_mode=args.value_mode,
        value_column="benzene_ppbv_equivalent",
    )
    plot_kwargs = calendar_colormap_kwargs(
        series=series,
        value_mode=args.value_mode,
        colormap_name=args.colormap,
    )

    fig, ax = calplot.calplot(
        series,
        suptitle=args.title or default_title_from_path(args.input_tsv),
        figsize=(12, 3.2),
        colorbar=(args.value_mode != "presence"),
        **plot_kwargs,
    )
    year_axes = flatten_axes(ax)
    plot_years = sorted(date_index.year.unique())

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

    if args.output:
        output_path = Path(args.output).expanduser().resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_path, dpi=args.dpi, bbox_inches="tight")

    if args.no_show:
        plt.close(fig)
    else:
        plt.show()
        plt.close(fig)

    return fig


if __name__ == "__main__":
    raise SystemExit(main())
