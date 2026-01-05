"""
Yardstick Engine - Local-first benchmark execution core.

The Yardstick OSS Engine is a local-first execution core for running
custom benchmarks defined as portable YAML/JSON specs against one or
more black-box systems via HTTP, producing deterministic scores and
structured results.
"""

__version__ = "0.1.0"

# Public API
from engine.spec import (
    BenchmarkSpec,
    load_spec,
    SpecLoadError,
)
from engine.dataset import (
    Case,
    load_dataset_jsonl,
    DatasetLoadError,
)
from engine.jsonpath import (
    eval_jsonpath,
    JSONPathError,
)

__all__ = [
    "__version__",
    # Spec
    "BenchmarkSpec",
    "load_spec",
    "SpecLoadError",
    # Dataset
    "Case",
    "load_dataset_jsonl",
    "DatasetLoadError",
    # JSONPath
    "eval_jsonpath",
    "JSONPathError",
]

