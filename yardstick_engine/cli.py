"""
CLI entrypoint for the Yardstick engine.
"""

import argparse
import sys


def main() -> int:
    """Main CLI entrypoint."""
    parser = argparse.ArgumentParser(
        prog="yardstick",
        description="Yardstick benchmark engine CLI",
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # validate command (placeholder)
    validate_parser = subparsers.add_parser("validate", help="Validate a benchmark spec")
    validate_parser.add_argument("spec", help="Path to benchmark spec file")
    
    # run command (placeholder)
    run_parser = subparsers.add_parser("run", help="Run a benchmark")
    run_parser.add_argument("spec", help="Path to benchmark spec file")
    run_parser.add_argument(
        "--system",
        action="append",
        dest="systems",
        help="System to evaluate (format: name=url)",
    )
    run_parser.add_argument("--out", help="Output file for results JSON")
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        return 0
    
    if args.command == "validate":
        print(f"[validate] Not yet implemented. Spec: {args.spec}")
        return 0
    
    if args.command == "run":
        print(f"[run] Not yet implemented. Spec: {args.spec}")
        return 0
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

