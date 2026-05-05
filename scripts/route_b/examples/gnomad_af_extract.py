#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
from pathlib import Path


def write_variant(line: str, headers: list[str]) -> str:
    fields = line.rstrip("\n").split("\t")
    out = ""
    if fields[headers.index("FILTER")] == "PASS" and len(fields[headers.index("ALT")].split(",")) == 1:
        row = fields[:7]
        for token in fields[headers.index("INFO")].split(";"):
            if token.startswith("AF="):
                _, value = token.split("=", 1)
                row.append(f"AF={float(value):f}")
        out = "\t".join(row) + "\n"
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_vcf_gz")
    parser.add_argument("output_vcf")
    args = parser.parse_args()

    headers: list[str] = []
    with gzip.open(args.input_vcf_gz, "rt") as src, open(args.output_vcf, "w", encoding="utf-8") as dst:
        for line in src:
            if line.startswith("#") and not line.startswith("##INFO"):
                if line.startswith("#CHROM"):
                    headers = line.strip().replace("#", "").split("\t")
                dst.write(line)
            elif line.startswith("##INFO=<ID=AF,"):
                dst.write(line)
            elif not line.startswith("#"):
                dst.write(write_variant(line, headers))


if __name__ == "__main__":
    main()
