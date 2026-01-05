"""
Yardstick Benchmark Runner

Edit this file to configure and run your benchmarks.
"""

from pathlib import Path
from engine import load_spec, load_dataset_jsonl, run_benchmark, SystemConfig


# === CONFIGURATION ===

# Path to your benchmark spec
BENCHMARK = "benchmarks/trivia_qa/benchmark.yaml"

# Systems to test (name -> endpoint)
SYSTEMS = [
    SystemConfig(name="openai-gpt-4o-mini", endpoint="http://localhost:8001/solve"),
    SystemConfig(name="groq-llama-3.1-8b-instant", endpoint="http://localhost:8002/solve"),
]

# Output file (optional)
OUTPUT_FILE = "results.json"


# === RUN ===

def main():
    # Load benchmark
    spec_path = Path(BENCHMARK)
    spec = load_spec(spec_path)
    dataset_path = spec_path.parent / spec.dataset.path
    cases = load_dataset_jsonl(dataset_path)
    
    print(f"Benchmark: {spec.name} (v{spec.version})")
    print(f"Dataset: {len(cases)} cases")
    print(f"Systems: {', '.join(s.name for s in SYSTEMS)}")
    print()
    
    # Run
    result = run_benchmark(spec, cases, SYSTEMS)
    
    # Print results
    for sys_result in result.systems:
        rate = sys_result.aggregates.get("exact_match_rate", 0)
        errors = sum(sys_result.error_counts.values())
        print(f"{sys_result.system_name}: {rate:.1%} ({errors} errors)")
    
    # Save results
    if OUTPUT_FILE:
        Path(OUTPUT_FILE).write_text(result.model_dump_json(indent=2))
        print(f"\nResults saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()

