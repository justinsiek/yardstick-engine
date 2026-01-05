# Yardstick Engine

Local-first benchmark execution core for evaluating systems via HTTP.

## Quick Start

**1. Install**

```bash
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

**2. Start the demo server** (Terminal 1)

```bash
python demo_server.py
```

**3. Run the benchmark** (Terminal 2)

```bash
python run.py
```

That's it! You'll see results like:

```
Benchmark: Addition QA (v1)
Dataset: 10 cases

demo: 100.0% (0 errors)

Results saved to results.json
```

## Using Your Own System

Edit `run.py` to point to your endpoint:

```python
SYSTEMS = [
    SystemConfig(name="my_system", endpoint="http://localhost:8000/solve"),
]
```

Your endpoint should accept POST requests with JSON body `{"input": {...}}` and return `{"answer": "..."}`.

## Development

```bash
pytest  # Run tests
```
