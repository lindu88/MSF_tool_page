#!/usr/bin/env python3

"""Convert line-oriented NISTLOG .txt files into a strict 5-column TSV."""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

UNKNOWN_LINE_RE = re.compile(r"^Unknown:\s*\|(?P<sample>[^|]+)\|.*?\|IS(?P<area>\d+(?:\.\d+)?)\|")
HIT_LINE_RE = re.compile(
    r"^Hit\s*1\s*:\s*(?:<<(?P<compound_bracket>[^>]+)>>|(?P<compound_plain>[^;]+)).*?CAS:\s*(?P<cas>[^;\r\n]+)",
    re.IGNORECASE,
)
SOURCE_TOKEN_RE = re.compile(r"_([A-Za-z0-9]+)_C\d+_C\d+_elu$")
SINGLE_UNDERSCORE_TIME_RE = re.compile(r"^(\d+_\d{4}_\d{2}_\d{2})_(\d{2}H\d{2}_.+)$")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Convert a line-oriented NISTLOG .txt file into the strict 5-column "
            "TSV used by MSF_calplot_tsv.py and MSF_hourplot.py."
        )
    )
    parser.add_argument(
        "input_txt",
        help="Path to the NISTLOG .txt file.",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output TSV path. Defaults to <input-stem>.tsv in the same directory.",
    )
    return parser


def normalize_sample_name(sample_name: str) -> str:
    match = SINGLE_UNDERSCORE_TIME_RE.fullmatch(sample_name)
    if not match:
        return sample_name
    return f"{match.group(1)}__{match.group(2)}"


def format_area(raw_area: str) -> str:
    if re.fullmatch(r"\d+", raw_area):
        return f"{int(raw_area):,}"
    if re.fullmatch(r"\d+\.\d+", raw_area):
        whole, frac = raw_area.split(".", 1)
        return f"{int(whole):,}.{frac}"
    raise ValueError(f"Integrated area {raw_area!r} is not numeric.")


def derive_source(sample_name: str, path: Path, line_number: int) -> str:
    match = SOURCE_TOKEN_RE.search(sample_name)
    if not match:
        raise ValueError(
            f"{path} line {line_number}: could not derive source from sample name "
            f"{sample_name!r}"
        )

    token = match.group(1).upper()
    if "AMB" in token:
        return "AMB"
    if "CAL" in token:
        return "CAL"
    if "CYL" in token:
        return "CYL"

    letters_only = re.sub(r"[^A-Z]", "", token)
    if 2 <= len(letters_only) <= 6:
        return letters_only

    raise ValueError(
        f"{path} line {line_number}: unsupported source token {token!r} in "
        f"sample name {sample_name!r}"
    )


def parse_unknown_line(line: str, path: Path, line_number: int) -> tuple[str, str, str]:
    match = UNKNOWN_LINE_RE.search(line)
    if not match:
        raise ValueError(f"{path} line {line_number}: malformed Unknown line.")

    sample_name = normalize_sample_name(match.group("sample").strip())
    area = format_area(match.group("area").strip())
    source = derive_source(sample_name, path, line_number)
    return source, sample_name, area


def parse_hit_line(line: str, path: Path, line_number: int) -> tuple[str, str]:
    match = HIT_LINE_RE.search(line)
    if not match:
        raise ValueError(f"{path} line {line_number}: malformed Hit 1 line.")

    compound_name = (
        match.group("compound_bracket")
        if match.group("compound_bracket") is not None
        else match.group("compound_plain")
    )
    compound_name = compound_name.strip()
    cas_number = match.group("cas").strip()

    if not compound_name:
        raise ValueError(f"{path} line {line_number}: compound name is blank.")
    if not cas_number:
        raise ValueError(f"{path} line {line_number}: CAS number is blank.")

    return compound_name, cas_number


def convert_nistlog_file(
    input_txt: str | Path,
    *,
    output: str | Path | None = None,
) -> dict[str, object]:
    input_path = Path(input_txt).expanduser().resolve()
    if not input_path.is_file():
        raise ValueError(f"{input_path} is not a file.")

    output_path = (
        Path(output).expanduser().resolve()
        if output is not None
        else input_path.with_suffix(".tsv")
    )

    lines = input_path.read_text(encoding="utf-8", errors="replace").splitlines()
    rows_out: list[list[str]] = []
    logical_line_count = 0

    index = 0
    while index < len(lines):
        line = lines[index].strip()
        if not line:
            index += 1
            continue

        logical_line_number = index + 1
        logical_line_count += 1
        if not line.startswith("Unknown:"):
            raise ValueError(
                f"{input_path} line {logical_line_number}: expected an Unknown line, "
                f"found {line!r}"
            )
        if index + 1 >= len(lines):
            raise ValueError(
                f"{input_path} line {logical_line_number}: missing Hit 1 line after "
                "Unknown line."
            )

        hit_line = lines[index + 1].strip()
        hit_line_number = index + 2
        try:
            source, sample_name, area = parse_unknown_line(line, input_path, logical_line_number)
            compound_name, cas_number = parse_hit_line(hit_line, input_path, hit_line_number)
            rows_out.append([source, sample_name, area, compound_name, cas_number])
        except ValueError as e:
            print(f"skipping line due to error:, {e}")
            continue

        index += 2

    if not rows_out:
        raise ValueError(f"{input_path} did not contain any Unknown/Hit 1 records.")

    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerows(rows_out)

    return {
        "input_path": input_path,
        "output_path": output_path,
        "row_count": len(rows_out),
        "line_count": logical_line_count,
    }


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = convert_nistlog_file(args.input_txt, output=args.output)
    print(f"Input: {result['input_path']}")
    print(f"Output: {result['output_path']}")
    print(f"Rows written: {result['row_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
