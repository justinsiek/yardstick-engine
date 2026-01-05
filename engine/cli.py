"""
CLI entrypoint for the Yardstick engine.

Commands:
- validate: Validate a benchmark spec and its dataset
- run: Run a benchmark against one or more systems
"""

import argparse
import json
import sys
from pathlib import Path

from engine.dataset import DatasetLoadError, load_dataset_jsonl
from engine.results import RunResult
from engine.runner import run_benchmark
from engine.spec import SpecLoadError, load_spec
from engine.systems import SystemConfig


def _resolve_dataset_path(spec_path: Path, dataset_path: str) -> Path:
    """
    Resolve the dataset path relative to the spec file.
    
    If dataset_path is absolute, use it directly.
    Otherwise, resolve it relative to the spec file's directory.
    """
    dataset = Path(dataset_path)
    if dataset.is_absolute():
        return dataset
    return spec_path.parent / dataset


def _print_error(message: str) -> None:
    """Print an error message to stderr."""
    print(f"Error: {message}", file=sys.stderr)


def _print_success(message: str) -> None:
    """Print a success message."""
    print(f"✓ {message}")


def cmd_validate(args: argparse.Namespace) -> int:
    """
    Validate a benchmark spec and its dataset.
    
    Returns:
        0 on success, 1 on validation failure
    """
    spec_path = Path(args.spec)
    
    # Validate spec
    try:
        spec = load_spec(spec_path)
    except SpecLoadError as e:
        _print_error(f"Invalid spec: {e}")
        return 1
    
    _print_success(f"Spec valid: {spec.id} (v{spec.version})")
    
    # Validate dataset
    dataset_path = _resolve_dataset_path(spec_path, spec.dataset.path)
    try:
        cases = load_dataset_jsonl(dataset_path)
    except DatasetLoadError as e:
        _print_error(f"Invalid dataset: {e}")
        return 1
    
    _print_success(f"Dataset valid: {len(cases)} cases")
    
    print(f"\nBenchmark '{spec.name}' is valid.")
    return 0


def _parse_system(system_str: str) -> SystemConfig:
    """
    Parse a system string in format 'name=url'.
    
    Raises:
        ValueError: If the format is invalid
    """
    if "=" not in system_str:
        raise ValueError(f"Invalid system format: '{system_str}'. Expected 'name=url'")
    
    name, url = system_str.split("=", 1)
    name = name.strip()
    url = url.strip()
    
    if not name:
        raise ValueError("System name cannot be empty")
    if not url:
        raise ValueError("System URL cannot be empty")
    
    return SystemConfig(name=name, endpoint=url)


def _print_run_summary(result: RunResult) -> None:
    """Print a summary of the benchmark run."""
    print(f"\n{'='*60}")
    print(f"Benchmark: {result.benchmark_id} (v{result.benchmark_version})")
    print(f"Duration: {(result.finished_at - result.started_at).total_seconds():.2f}s")
    print(f"{'='*60}")
    
    for sys_result in result.systems:
        print(f"\nSystem: {sys_result.system_name}")
        
        # Print aggregates
        for name, value in sys_result.aggregates.items():
            print(f"  {name}: {value:.2%}")
        
        # Print error counts if any
        if sys_result.error_counts:
            total_errors = sum(sys_result.error_counts.values())
            print(f"  Errors: {total_errors}")
            for code, count in sorted(sys_result.error_counts.items()):
                print(f"    - {code}: {count}")
        
        # Summary stats
        total_cases = len(sys_result.case_results)
        error_cases = sum(sys_result.error_counts.values()) if sys_result.error_counts else 0
        success_cases = total_cases - error_cases
        print(f"  Cases: {success_cases}/{total_cases} successful")


def cmd_run(args: argparse.Namespace) -> int:
    """
    Run a benchmark against one or more systems.
    
    Returns:
        0 on success (even if some cases error), 1 on validation failure
    """
    spec_path = Path(args.spec)
    
    # Validate spec
    try:
        spec = load_spec(spec_path)
    except SpecLoadError as e:
        _print_error(f"Invalid spec: {e}")
        return 1
    
    # Validate dataset
    dataset_path = _resolve_dataset_path(spec_path, spec.dataset.path)
    try:
        cases = load_dataset_jsonl(dataset_path)
    except DatasetLoadError as e:
        _print_error(f"Invalid dataset: {e}")
        return 1
    
    # Parse systems
    if not args.systems:
        _print_error("At least one --system is required")
        return 1
    
    systems: list[SystemConfig] = []
    for system_str in args.systems:
        try:
            systems.append(_parse_system(system_str))
        except ValueError as e:
            _print_error(str(e))
            return 1
    
    # Print run info
    print(f"Running benchmark: {spec.name}")
    print(f"Dataset: {len(cases)} cases")
    print(f"Systems: {', '.join(s.name for s in systems)}")
    print()
    
    # Run benchmark
    result = run_benchmark(spec, cases, systems)
    
    # Print summary
    _print_run_summary(result)
    
    # Write results if --out specified
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Serialize to JSON
        result_json = result.model_dump_json(indent=2)
        out_path.write_text(result_json, encoding="utf-8")
        print(f"\nResults written to: {out_path}")
    
    # Exit 0 even if some cases errored (per spec)
    return 0


def main() -> int:
    """Main CLI entrypoint."""
    parser = argparse.ArgumentParser(
        prog="yardstick",
        description="Yardstick benchmark engine CLI",
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # validate command
    validate_parser = subparsers.add_parser(
        "validate", 
        help="Validate a benchmark spec and its dataset"
    )
    validate_parser.add_argument(
        "spec", 
        help="Path to benchmark spec file (YAML or JSON)"
    )
    
    # run command
    run_parser = subparsers.add_parser(
        "run", 
        help="Run a benchmark against one or more systems"
    )
    run_parser.add_argument(
        "spec", 
        help="Path to benchmark spec file (YAML or JSON)"
    )
    run_parser.add_argument(
        "--system",
        action="append",
        dest="systems",
        metavar="NAME=URL",
        help="System to evaluate (format: name=url). Can be specified multiple times.",
    )
    run_parser.add_argument(
        "--out", 
        metavar="FILE",
        help="Output file for results JSON"
    )
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        return 0
    
    if args.command == "validate":
        return cmd_validate(args)
    
    if args.command == "run":
        return cmd_run(args)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
