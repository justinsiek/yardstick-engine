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
from engine.spec import load_spec
from engine.dataset import load_dataset_jsonl
from engine.eval import run_benchmark
from engine.systems import SystemConfig

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

## CLI Usage

```bash
# Validate a benchmark spec
yardstick validate benchmarks/addition_qa_v1/benchmark.yaml

# Run a benchmark
yardstick run benchmarks/addition_qa_v1/benchmark.yaml \
  --system my_system=http://localhost:8000/solve \
  --out results.json
```

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest
```

