# Yardstick Engine

Local-first execution core for running custom benchmarks.

## Overview

The Yardstick OSS Engine is a local-first execution core for running custom benchmarks defined as portable YAML/JSON specs against one or more black-box systems via HTTP, producing deterministic scores and structured results.

## Installation

```bash
# Development install
pip install -e ".[dev]"
```

## Quick Start

```python
from engine import load_spec, load_dataset_jsonl, run_benchmark, SystemConfig

# Load benchmark
spec = load_spec("benchmarks/addition_qa_v1/benchmark.yaml")
cases = load_dataset_jsonl("benchmarks/addition_qa_v1/dataset.jsonl")

# Define systems to evaluate
systems = [
    SystemConfig(name="my_system", endpoint="http://localhost:8000/solve"),
]

# Run benchmark
result = run_benchmark(spec, cases, systems)
```

See `run.py` for a complete example.

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest
```

