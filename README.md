# Yardstick Engine

Local-first benchmark execution core for evaluating systems via HTTP.

## Quick Start

**1. Install**

```bash
python -m venv venv
source venv/bin/activate
pip install -e ".[dev,proxy]"
```

**2. Set up your API key**

```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

**3. Start the proxy** (Terminal 1)

```bash
python proxies/openai_proxy.py
```

**4. Run the benchmark** (Terminal 2)

```bash
python run.py
```

---

## Creating Your Own Benchmark

A benchmark needs two files in a folder:

```
benchmarks/my_benchmark/
├── benchmark.yaml    # Configuration
└── dataset.jsonl     # Test cases
```

### dataset.jsonl

One test case per line. Each case has:
- `id` – unique identifier
- `input` – sent to your system
- `reference` – the expected answer

```json
{"id": "q1", "input": {"question": "What is 2+2?"}, "reference": {"answer": "4"}}
{"id": "q2", "input": {"question": "Capital of France?"}, "reference": {"answer": "Paris"}}
```

### benchmark.yaml

```yaml
id: my_benchmark
name: My Benchmark
version: 1

dataset:
  path: dataset.jsonl

contract:
  protocol: http
  request:
    method: POST
    body_json_path: "$.input"        # What to send (from each case's input)
  response:
    output_json_path: "$.answer"     # Where to find the answer in the response

scoring:
  metrics:
    - name: exact_match
      type: exact_match
      args:
        pred_path: "$"               # The extracted response
        ref_path: "$.answer"         # Path in reference to compare against
        normalize:
          lowercase: true
          strip_whitespace: true
  primary_metric: exact_match

reporting:
  aggregate:
    - name: exact_match_rate
      type: mean
      metric: exact_match
```

### What to Change

| Field | What it does |
|-------|-------------|
| `id`, `name` | Identify your benchmark |
| `dataset.path` | Path to your JSONL file |
| `body_json_path` | What part of `input` to send (usually `$.input`) |
| `output_json_path` | Where the answer is in the HTTP response |
| `ref_path` | Where the expected answer is in `reference` |

Then update `run.py`:

```python
BENCHMARK = "benchmarks/my_benchmark/benchmark.yaml"
```

---

## Using Your Own System

Your HTTP endpoint should:
- Accept `POST` requests with JSON body (the case's `input`)
- Return JSON with the answer at the path you specified in `output_json_path`

Example request/response:

```
POST /solve
{"question": "What is 2+2?"}

Response:
{"answer": "4"}
```

---

## Development

```bash
pytest  # Run tests
```
