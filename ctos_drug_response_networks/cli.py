from __future__ import annotations

import argparse
from pathlib import Path
from datetime import datetime, timezone
import json
import sys

from .config import load_config, dump_json
from .sample_map import write_sample_map
from .validators import validate_assets
from .leakage import scan_repo, write_leakage_report, fail_if_hits
from .route_b import describe_route_b
from .runner import reproduce
from .utils import make_run_id
from .errors import CtosReproError


def _figure_list(value: str, config: dict) -> list[str]:
    if value == "all":
        return list(config["figures"]["enabled_families"])
    return [value]


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ctos-repro")
    sub = parser.add_subparsers(dest="command", required=True)

    rep = sub.add_parser("reproduce")
    rep.add_argument("--route", choices=["derived", "raw"], required=True)
    rep.add_argument("--figure", choices=["all", "fig2", "fig3", "fig4", "fig5", "fig6"], required=True)
    rep.add_argument("--config", required=True)
    rep.add_argument("--outdir", default="outputs")
    rep.add_argument("--strict", action="store_true")
    rep.add_argument("--overwrite", action="store_true")
    rep.add_argument("--run-id")

    val = sub.add_parser("validate-assets")
    val.add_argument("--config", required=True)

    leak = sub.add_parser("scan-leakage")
    leak.add_argument("--repo-root", required=True)
    leak.add_argument("--config", default="config/default.yaml")

    sm = sub.add_parser("build-sample-map")
    sm.add_argument("--metadata", required=True)
    sm.add_argument("--out", required=True)

    rb = sub.add_parser("describe-route-b")
    rb.add_argument("--config", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = make_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "build-sample-map":
            df = write_sample_map(args.metadata, args.out)
            print(f"Wrote {len(df)} rows to {args.out}")
            return 0

        config = load_config(args.config)
        config_path = Path(args.config)

        if args.command == "validate-assets":
            report = validate_assets(config, config_path=config_path)
            print("Asset validation passed.")
            print(report)
            return 0

        if args.command == "scan-leakage":
            report = scan_repo(args.repo_root, config["policy"]["forbidden_strings"])
            report_path = Path(args.repo_root) / "logs/leakage_scan.json"
            write_leakage_report(report_path, report)
            fail_if_hits(report)
            print(f"Leakage scan passed: {report_path}")
            return 0

        if args.command == "describe-route-b":
            print(describe_route_b(config))
            return 0

        if args.command == "reproduce":
            figure_list = _figure_list(args.figure, config)
            validate_assets(config, config_path=config_path, requested_figures=figure_list)
            run_id = args.run_id or make_run_id()
            outdir = Path(args.outdir)
            outputs = reproduce(config, args.route, figure_list, outdir)
            manifest = {
                "run_id": run_id,
                "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
                "route": args.route,
                "figures_requested": figure_list,
                "inputs": [str(Path(args.config))],
                "outputs": outputs,
                "status": "success",
                "warnings": [],
            }
            dump_json(outdir / f"logs/{run_id}_manifest.json", manifest)
            validation_report = {"status": "ok", "requested_figures": figure_list, "output_count": len(outputs)}
            dump_json(outdir / f"logs/{run_id}_validation.json", validation_report)
            print(json.dumps(manifest, indent=2, ensure_ascii=False))
            return 0

        parser.print_help()
        return 1
    except CtosReproError as exc:
        print(str(exc), file=sys.stderr)
        return getattr(exc, "exit_code", 1)


if __name__ == "__main__":
    raise SystemExit(main())
