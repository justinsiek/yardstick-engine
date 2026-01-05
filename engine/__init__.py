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
from engine.extraction import (
    extract_output,
    ExtractionError,
)
from engine.metrics import (
    score_exact_match,
    MetricError,
)
from engine.aggregation import (
    aggregate_mean,
)
from engine.systems import (
    SystemConfig,
    invoke_case,
    InvokeError,
)
from engine.results import (
    ErrorInfo,
    CaseResult,
    SystemResult,
    RunResult,
)
from engine.runner import (
    run_benchmark,
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
    # Extraction
    "extract_output",
    "ExtractionError",
    # Metrics
    "score_exact_match",
    "MetricError",
    # Aggregation
    "aggregate_mean",
    # Systems
    "SystemConfig",
    "invoke_case",
    "InvokeError",
    # Results
    "ErrorInfo",
    "CaseResult",
    "SystemResult",
    "RunResult",
    # Runner
    "run_benchmark",
]
