#!/usr/bin/env python3

"""Convert raw UTF-16 search-output .txt files into a strict 5-column TSV."""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

UNKNOWN_RE = re.compile(r"Unknown:\s*\|([^|]+)\|.*?\|IS(\d+(?:\.\d+)?)\|", re.S)
HIT_RE = re.compile(r"Hit\s*1\s*:\s*(.+)")
CAS_RE = re.compile(r"CAS:\s*([0-9-]+)")
SOURCE_TOKEN_RE = re.compile(r"_([A-Za-z0-9]+)_C\d+_C\d+_elu$")
SINGLE_UNDERSCORE_TIME_RE = re.compile(r"^(\d+_\d{4}_\d{2}_\d{2})_(\d{2}H\d{2}_.+)$")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convert raw UTF-16 search-output .txt files into a strict 5-column TSV."
    )
    parser.add_argument(
        "data_dir",
        help="Directory containing the raw .txt search-output files.",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output TSV path. Defaults to <data-dir>/search_output.tsv",
    )
    parser.add_argument(
        "--glob",
        default="*.txt",
        help="Glob pattern used to find raw text files.",
    )
    parser.add_argument(
        "--fail-on-error",
        action="store_true",
        help="Abort on the first malformed block instead of skipping it.",
    )
    return parser


def derive_source(sample_name: str, path: Path, block_number: int) -> str:
    match = SOURCE_TOKEN_RE.search(sample_name)
    if not match:
        raise ValueError(
            f"{path} block {block_number}: could not derive source from sample name "
            f"{sample_name!r}"
        )

    token = match.group(1).upper()
    if token.startswith("AMB"):
        return "AMB"
    if token.startswith("CAL"):
        return "CAL"
    if token.startswith("CYL"):
        return "CYL"
    return token[:3]


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


def parse_block(block: str, path: Path, block_number: int) -> list[str]:
    unknown_match = UNKNOWN_RE.search(block)
    hit_match = HIT_RE.search(block)
    cas_match = CAS_RE.search(block)

    if not unknown_match:
        raise ValueError(f"{path} block {block_number}: missing Unknown/IS line.")
    if not hit_match:
        raise ValueError(f"{path} block {block_number}: missing 'Hit 1' line.")
    if not cas_match:
        raise ValueError(f"{path} block {block_number}: missing CAS number.")

    sample_name, raw_area = unknown_match.groups()
    sample_name = normalize_sample_name(sample_name.strip())
    area = format_area(raw_area.strip())
    compound_name = hit_match.group(1).strip()
    cas_number = cas_match.group(1).strip()
    source = derive_source(sample_name, path, block_number)

    if not compound_name:
        raise ValueError(f"{path} block {block_number}: compound name is blank.")

    return [source, sample_name, area, compound_name, cas_number]


def convert_directory(
    data_dir: str | Path,
    *,
    output: str | Path | None = None,
    glob_pattern: str = "*.txt",
    fail_on_error: bool = False,
) -> dict[str, object]:
    data_dir_path = Path(data_dir).expanduser().resolve()
    if not data_dir_path.is_dir():
        raise ValueError(f"{data_dir_path} is not a directory.")

    output_path = (
        Path(output).expanduser().resolve()
        if output is not None
        else (data_dir_path / "search_output.tsv")
    )
    txt_paths = sorted(data_dir_path.glob(glob_pattern))
    if not txt_paths:
        raise ValueError(f"No files matched {glob_pattern!r} in {data_dir_path}")

    rows_out: list[list[str]] = []
    counts: list[tuple[str, int]] = []
    skipped: list[str] = []

    for path in txt_paths:
        count = 0
        data = path.read_bytes()

        if len(data) % 2:
            data = data[:-1]

        text = data.decode("utf-16")
        blocks = [block.strip() for block in text.split("\f") if block.strip()]
        for block_number, block in enumerate(blocks, start=1):
            try:
                row = parse_block(block, path, block_number)
            except ValueError as exc:
                if fail_on_error:
                    raise
                skipped.append(str(exc))
                continue
            rows_out.append(row)
            count += 1
        counts.append((path.name, count))

    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerows(rows_out)

    return {
        "output_path": output_path,
        "file_count": len(txt_paths),
        "row_count": len(rows_out),
        "counts": counts,
        "skipped": skipped,
    }


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = convert_directory(
        args.data_dir,
        output=args.output,
        glob_pattern=args.glob,
        fail_on_error=args.fail_on_error,
    )

    print(f"Output: {result['output_path']}")
    print(f"Files parsed: {result['file_count']}")
    print(f"Rows written: {result['row_count']}")
    print(f"Blocks skipped: {len(result['skipped'])}")
    for name, count in result["counts"]:
        print(f"  {name}: {count}")
    if result["skipped"]:
        print("Skipped blocks:")
        for message in result["skipped"]:
            print(f"  {message}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
