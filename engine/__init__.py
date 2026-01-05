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

__all__ = [
    "__version__",
    "BenchmarkSpec",
    "load_spec",
    "SpecLoadError",
]

