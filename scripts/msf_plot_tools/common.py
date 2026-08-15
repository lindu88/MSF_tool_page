from __future__ import annotations

import csv
import re
from collections.abc import Iterable
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Circle

SITE_RE = re.compile(r"[A-Z]{2,6}")
SAMPLE_NAME_RE = re.compile(r"^\d+_\d{4}_\d{2}_\d{2}__\d{2}H\d{2}_.+$")
DATE_RE = re.compile(r"(\d{4})_(\d{2})_(\d{2})")
NUMERIC_VALUE_RE = re.compile(r"[\d,]+(?:\.\d+)?")
CAS_RE = re.compile(r"\d{2,7}-\d{2}-\d")
DEFAULT_NULL_COLOR = "#808080"
DEFAULT_NULL_INSET = 0.29


def normalize_site_filter(site_filter: str | None) -> str | None:
    if site_filter is None:
        return None
    text = str(site_filter).strip()
    if not text or text.upper() in {"ALL", "NONE"}:
        return None
    return text.upper()


def parse_date_from_sample(sample_name: str) -> pd.Timestamp:
    match = DATE_RE.search(str(sample_name))
    if not match:
        return pd.NaT
    year, month, day = match.groups()
    return pd.to_datetime(f"{year}-{month}-{day}", errors="coerce")


def parse_hour_from_sample(sample_name: str) -> int | None:
    match = re.search(r"__\s*(\d{2})H(\d{2})", str(sample_name))
    if not match:
        return None
    hour_text, _minute_text = match.groups()
    try:
        hour = int(hour_text)
    except ValueError:
        return None
    return hour if 0 <= hour <= 23 else None


def parse_numeric_value(raw_value: object) -> float:
    text = str(raw_value).strip().replace(",", "")
    match = re.fullmatch(r"\d+(?:\.\d+)?", text)
    if not match:
        raise ValueError(f"Value {raw_value!r} is not numeric.")
    return float(match.group(0))


def normalize_cas_value(raw_value: object) -> str | pd.NA:
    text = str(raw_value).strip()
    return text if CAS_RE.fullmatch(text) else pd.NA


def build_plot_name(compound_name: str, cas_number: object) -> str:
    compound_text = str(compound_name).strip()
    cas_text = normalize_cas_value(cas_number)
    if pd.isna(cas_text):
        return compound_text
    return f"{compound_text} (CAS: {cas_text})"


def safe_filename(text: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "_", str(text)).strip("_")
    return slug or "plot"


def default_title_from_path(path: str | Path) -> str:
    return Path(path).expanduser().resolve().stem.replace("-", " ")


def ensure_output_dir(output_dir: str | Path | None) -> Path | None:
    if output_dir in (None, "", False):
        return None
    path = Path(output_dir).expanduser().resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def format_title_suffix(title_suffix: str | None) -> str:
    text = "" if title_suffix is None else str(title_suffix).strip()
    return f" ({text})" if text else ""


def sample_colormap_color(colormap_name: str, position: float):
    return plt.get_cmap(colormap_name)(position)


def validate_search_results_row(row, line_number: int, path: Path) -> dict[str, str]:
    if len(row) != 5:
        raise ValueError(
            f"{path} line {line_number}: expected 5 tab-separated columns, "
            f"found {len(row)}: {row!r}"
        )

    site, sample_name, integrated_signal, compound_name, cas_number = [
        str(cell).strip() for cell in row
    ]

    problems = []
    if not SITE_RE.fullmatch(site):
        problems.append(
            f"column 1 must be an uppercase site code like AMB/CAL, got {site!r}"
        )
    if not SAMPLE_NAME_RE.fullmatch(sample_name):
        problems.append(
            "column 2 must look like a sample filename such as "
            "'00004_2025_01_01__06H19_AMB60_C6_C12_elu'"
        )
    if not NUMERIC_VALUE_RE.fullmatch(integrated_signal):
        problems.append(
            f"column 3 must be a numeric integrated area, got {integrated_signal!r}"
        )
    if not compound_name:
        problems.append("column 4 must contain a compound name")
    if not cas_number:
        problems.append("column 5 must contain a CAS number or source label")

    if problems:
        raise ValueError(f"{path} line {line_number}: " + "; ".join(problems))

    return {
        "site": site,
        "sample_name": sample_name,
        "integrated_signal": integrated_signal,
        "compound_name": compound_name,
        "cas_number": cas_number,
    }


def load_strict_search_results_tsv(tsv_path: str | Path) -> pd.DataFrame:
    path = Path(tsv_path).expanduser().resolve()
    if path.suffix.lower() != ".tsv":
        raise ValueError(f"{path} is not a .tsv file.")

    rows = []
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle, delimiter="\t")
        for line_number, row in enumerate(reader, start=1):
            rows.append(validate_search_results_row(row, line_number, path))

    if not rows:
        raise ValueError(f"{path} is empty.")

    df = pd.DataFrame(rows)
    df["date"] = df["sample_name"].apply(parse_date_from_sample)
    df["hour"] = df["sample_name"].apply(parse_hour_from_sample)
    if df["date"].isna().any():
        bad_sample = df.loc[df["date"].isna(), "sample_name"].iloc[0]
        raise ValueError(
            f"{path}: could not parse a date from sample name {bad_sample!r}."
        )
    if df["hour"].isna().any():
        bad_sample = df.loc[df["hour"].isna(), "sample_name"].iloc[0]
        raise ValueError(
            f"{path}: could not parse an hour from sample name {bad_sample!r}."
        )

    df["integrated_signal"] = df["integrated_signal"].apply(parse_numeric_value)
    df["plot_name"] = df.apply(
        lambda row: build_plot_name(row["compound_name"], row["cas_number"]),
        axis=1,
    )
    df["hour"] = df["hour"].astype(int)
    return df


def validate_tic_summary_row(row, line_number: int, path: Path) -> dict[str, str]:
    if len(row) != 2:
        raise ValueError(
            f"{path} line {line_number}: expected 2 tab-separated columns, "
            f"found {len(row)}: {row!r}"
        )

    sample_name, benzene_equivalent = [str(cell).strip() for cell in row]
    problems = []
    if not SAMPLE_NAME_RE.fullmatch(sample_name):
        problems.append(
            "column 1 must look like a sample filename such as "
            "'00004_2025_01_01__06H19_AMB60_C6_C12_elu'"
        )
    if not NUMERIC_VALUE_RE.fullmatch(benzene_equivalent):
        problems.append(
            f"column 2 must be a numeric benzene-equivalent value, got {benzene_equivalent!r}"
        )

    if problems:
        raise ValueError(f"{path} line {line_number}: " + "; ".join(problems))

    return {
        "sample_name": sample_name,
        "benzene_ppbv_equivalent": benzene_equivalent,
    }


def load_strict_tic_summary_tsv(tsv_path: str | Path) -> pd.DataFrame:
    path = Path(tsv_path).expanduser().resolve()
    if path.suffix.lower() != ".tsv":
        raise ValueError(f"{path} is not a .tsv file.")

    rows = []
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle, delimiter="\t")
        for line_number, row in enumerate(reader, start=1):
            rows.append(validate_tic_summary_row(row, line_number, path))

    if not rows:
        raise ValueError(f"{path} is empty.")

    df = pd.DataFrame(rows)
    df["date"] = df["sample_name"].apply(parse_date_from_sample)
    if df["date"].isna().any():
        bad_sample = df.loc[df["date"].isna(), "sample_name"].iloc[0]
        raise ValueError(
            f"{path}: could not parse a date from sample name {bad_sample!r}."
        )

    df["benzene_ppbv_equivalent"] = df["benzene_ppbv_equivalent"].apply(
        parse_numeric_value
    )
    return df


def parse_iso_date(raw_value: object, line_number: int, path: Path, label: str):
    parsed = pd.to_datetime(str(raw_value).strip(), format="%Y-%m-%d", errors="coerce")
    if pd.isna(parsed):
        raise ValueError(
            f"{path} line {line_number}: {label} must be YYYY-MM-DD, got {raw_value!r}"
        )
    return parsed.normalize()


def load_null_periods_tsv(
    null_periods_path: str | Path | None,
) -> list[tuple[pd.Timestamp, pd.Timestamp]]:
    if null_periods_path in (None, "", False):
        return []

    path = Path(null_periods_path).expanduser().resolve()
    if path.suffix.lower() != ".tsv":
        raise ValueError(f"{path} is not a .tsv file.")

    periods = []
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle, delimiter="\t")
        for line_number, row in enumerate(reader, start=1):
            cleaned = [str(cell).strip() for cell in row]
            if not cleaned or not any(cleaned):
                continue
            if cleaned[0].startswith("#"):
                continue
            if len(cleaned) != 2:
                raise ValueError(
                    f"{path} line {line_number}: expected 2 tab-separated columns "
                    f"(start_date, end_date), found {len(cleaned)}: {row!r}"
                )
            start_date = parse_iso_date(cleaned[0], line_number, path, "start_date")
            end_date = parse_iso_date(cleaned[1], line_number, path, "end_date")
            if start_date > end_date:
                raise ValueError(
                    f"{path} line {line_number}: start_date {cleaned[0]!r} must be on "
                    f"or before end_date {cleaned[1]!r}"
                )
            periods.append((start_date, end_date))

    return periods


def null_dates_from_periods(
    null_periods: list[tuple[pd.Timestamp, pd.Timestamp]],
) -> pd.DatetimeIndex:
    if not null_periods:
        return pd.DatetimeIndex([])

    all_dates = set()
    for start_date, end_date in null_periods:
        all_dates.update(pd.date_range(start_date, end_date, freq="D"))
    return pd.DatetimeIndex(sorted(all_dates))


def build_date_index(
    data_dates: pd.Series | pd.DatetimeIndex, null_dates: pd.DatetimeIndex | None = None
) -> pd.DatetimeIndex:
    if len(data_dates) == 0 and (null_dates is None or len(null_dates) == 0):
        raise ValueError("No dates were available to build a plotting index.")

    date_start = min(data_dates) if len(data_dates) > 0 else null_dates.min()
    date_end = max(data_dates) if len(data_dates) > 0 else null_dates.max()
    if null_dates is not None and len(null_dates) > 0:
        date_start = min(date_start, null_dates.min())
        date_end = max(date_end, null_dates.max())
    return pd.date_range(date_start, date_end, freq="D")


def aggregate_daily_values(
    df: pd.DataFrame,
    date_index: pd.DatetimeIndex,
    value_mode: str,
    value_column: str,
) -> pd.Series:
    if value_mode == "presence":
        daily = df.groupby("date").size().astype(float)
        daily[:] = 1.0
    elif value_mode == "hit_count":
        daily = df.groupby("date").size().astype(float)
    elif value_mode == "max_value":
        daily = df.groupby("date")[value_column].max().astype(float)
    elif value_mode == "sum_value":
        daily = df.groupby("date")[value_column].sum().astype(float)
    else:
        raise ValueError(
            "value_mode must be one of: presence, hit_count, max_value, sum_value"
        )
    return daily.reindex(date_index, fill_value=0.0)


def calendar_colormap_kwargs(
    series: pd.Series, value_mode: str, colormap_name: str
) -> dict[str, object]:
    if value_mode != "hit_count":
        return {"cmap": colormap_name}

    max_count = max(1, int(series.max()))
    color_count = max_count + 1
    cmap = plt.get_cmap(colormap_name, color_count)
    return {"cmap": cmap, "vmin": -0.5, "vmax": max_count + 0.5}


def flatten_axes(ax):
    if isinstance(ax, Iterable) and not hasattr(ax, "get_position"):
        flattened = []
        for item in ax:
            flattened.extend(flatten_axes(item))
        return flattened
    return [ax]


def position_suptitle_close_to_calendar(fig, year_axes, gap: float = 0.015):
    if fig._suptitle is None:
        return

    calendar_positions = [year_ax.get_position().frozen() for year_ax in year_axes]
    if not calendar_positions:
        return

    calendar_top = max(position.y1 for position in calendar_positions)
    fig._suptitle.set_va("bottom")
    fig._suptitle.set_y(min(0.99, calendar_top + gap))


def resize_colorbar_to_calendar(fig, year_axes):
    colorbar_axes = [candidate for candidate in fig.axes if candidate not in year_axes]
    if len(colorbar_axes) != 1:
        return None

    calendar_positions = [year_ax.get_position().frozen() for year_ax in year_axes]
    if not calendar_positions:
        return None

    calendar_bottom = min(position.y0 for position in calendar_positions)
    calendar_top = max(position.y1 for position in calendar_positions)

    colorbar_ax = colorbar_axes[0]
    colorbar_position = colorbar_ax.get_position().frozen()
    colorbar_ax.set_position(
        [
            colorbar_position.x0,
            calendar_bottom,
            colorbar_position.width,
            calendar_top - calendar_bottom,
        ]
    )
    return colorbar_ax


def apply_weekday_layout(
    year_axes,
    *,
    monday_at_bottom: bool,
    days_on_left: bool,
):
    if monday_at_bottom:
        for year_ax in year_axes:
            year_ax.invert_yaxis()

    if days_on_left:
        for year_ax in year_axes:
            year_ax.yaxis.tick_left()
            year_ax.tick_params(labelleft=True, labelright=False)


def apply_hit_count_ticks(colorbar_ax, series: pd.Series):
    if colorbar_ax is None:
        return
    max_count = max(1, int(series.max()))
    tick_step = max(1, (max_count + 9) // 10)
    tick_values = list(range(0, max_count + 1, tick_step))
    if tick_values[-1] != max_count:
        tick_values.append(max_count)
    colorbar_ax.set_yticks(tick_values)


def colorbar_ticks_with_explicit_bounds(
    tick_values: list[float],
    min_value: float,
    max_value: float,
    *,
    min_gap_fraction: float = 0.5,
) -> list[float]:
    if max_value < min_value:
        raise ValueError("max_value must be greater than or equal to min_value")

    tick_values = sorted(
        set(
            float(tick)
            for tick in tick_values
            if min_value <= float(tick) <= max_value
        )
    )
    if not tick_values:
        return [min_value] if np.isclose(min_value, max_value) else [min_value, max_value]

    if len(tick_values) >= 2:
        steps = np.diff(tick_values)
        positive_steps = steps[steps > 0]
        typical_step = float(np.median(positive_steps)) if len(positive_steps) > 0 else None
    else:
        typical_step = None

    if not any(np.isclose(tick, min_value) for tick in tick_values):
        if typical_step is not None and (tick_values[0] - min_value) < (typical_step * min_gap_fraction):
            tick_values[0] = min_value
        else:
            tick_values.insert(0, min_value)

    tick_values = sorted(set(tick_values))

    if not any(np.isclose(tick, max_value) for tick in tick_values):
        if typical_step is not None and (max_value - tick_values[-1]) < (typical_step * min_gap_fraction):
            tick_values[-1] = max_value
        else:
            tick_values.append(max_value)

    return sorted(set(tick_values))


def apply_colorbar_data_bound_ticks(colorbar_ax, series: pd.Series):
    if colorbar_ax is None:
        return

    observed_values = series[pd.notna(series) & (series > 0)]
    if observed_values.empty:
        observed_values = series[pd.notna(series)]
    if observed_values.empty:
        return

    min_value = float(observed_values.min())
    max_value = float(observed_values.max())
    tick_values = colorbar_ticks_with_explicit_bounds(
        [float(tick) for tick in colorbar_ax.get_yticks()],
        min_value,
        max_value,
    )
    colorbar_ax.set_yticks(tick_values)


def apply_colorbar_bound_tick_labels(
    colorbar_ax,
    series: pd.Series,
    *,
    round_bounds_to_int: bool = False,
):
    if colorbar_ax is None:
        return

    observed_values = series[pd.notna(series) & (series > 0)]
    if observed_values.empty:
        observed_values = series[pd.notna(series)]
    if observed_values.empty:
        return

    min_value = float(observed_values.min())
    max_value = float(observed_values.max())
    tick_values = [float(tick) for tick in colorbar_ax.get_yticks()]
    labels = []

    for tick in tick_values:
        if round_bounds_to_int and (np.isclose(tick, min_value) or np.isclose(tick, max_value)):
            labels.append(str(int(round(tick))))
        elif np.isclose(tick, round(tick)):
            labels.append(str(int(round(tick))))
        else:
            labels.append(f"{tick:g}")

    colorbar_ax.set_yticklabels(labels)


def calendar_data_for_dates(marked_dates: pd.DatetimeIndex, year: int):
    year_dates = marked_dates[marked_dates.year == year]
    if len(year_dates) == 0:
        return None

    by_day = pd.Series(
        np.nan,
        index=pd.date_range(start=str(year), end=str(year + 1), freq="D")[:-1],
        dtype=float,
    )
    by_day.loc[year_dates] = 1.0
    by_day = pd.DataFrame(
        {
            "data": by_day,
            "day": by_day.index.dayofweek,
            "week": by_day.index.isocalendar().week,
        }
    )
    by_day.loc[(by_day.index.month == 1) & (by_day.week > 50), "week"] = 0
    by_day.loc[(by_day.index.month == 12) & (by_day.week < 10), "week"] = (
        by_day.week.max() + 1
    )

    plot_data = by_day.pivot(index="day", columns="week", values="data").values[::-1]
    return np.ma.masked_where(np.isnan(plot_data), plot_data)


def overlay_null_collection_periods(
    year_axes,
    plot_years: list[int],
    null_dates: pd.DatetimeIndex,
    null_color: str,
    null_inset: float = DEFAULT_NULL_INSET,
):
    if len(null_dates) == 0:
        return

    for year_ax, year in zip(year_axes, plot_years):
        null_data = calendar_data_for_dates(null_dates, year)
        if null_data is None:
            continue

        xlim = year_ax.get_xlim()
        ylim = year_ax.get_ylim()
        mask = np.ma.getmaskarray(null_data)
        radius = max(0.0, 0.5 - null_inset)
        for row_index, column_index in np.argwhere(~mask):
            year_ax.add_patch(
                Circle(
                    (column_index + 0.5, row_index + 0.5),
                    radius=radius,
                    facecolor=null_color,
                    edgecolor="none",
                    linewidth=0,
                    zorder=5,
                )
            )
        year_ax.set_xlim(xlim)
        year_ax.set_ylim(ylim)
