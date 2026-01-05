"""
Benchmark spec schema and loader for v1-min.

This module defines Pydantic models for the v1-min benchmark specification
and provides functions to load and validate specs from YAML/JSON files.
"""

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, model_validator

__all__ = [
    # Models
    "BenchmarkSpec",
    "DatasetConfig",
    "ContractConfig",
    "RequestConfig",
    "ResponseConfig",
    "ScoringConfig",
    "MetricConfig",
    "MetricArgs",
    "NormalizeConfig",
    "ReportingConfig",
    "AggregateConfig",
    # Loader
    "load_spec",
    "SpecLoadError",
]


# --- Nested models ---


class DatasetConfig(BaseModel):
    """Dataset configuration - where to find the benchmark cases."""
    
    path: str = Field(..., description="Path to JSONL dataset (relative to spec file or absolute)")


class RequestConfig(BaseModel):
    """HTTP request configuration."""
    
    method: Literal["POST"] = Field(..., description="HTTP method (must be POST in v1-min)")
    body_json_path: Literal["$.input"] = Field(
        ..., 
        description="JSONPath to extract request body from case (must be $.input in v1-min)"
    )


class ResponseConfig(BaseModel):
    """HTTP response configuration."""
    
    output_json_path: str = Field(
        ..., 
        description="JSONPath to extract output from response (use $ for full response)"
    )


class ContractConfig(BaseModel):
    """HTTP invocation contract configuration."""
    
    protocol: Literal["http"] = Field(..., description="Protocol (must be http in v1-min)")
    request: RequestConfig
    response: ResponseConfig


class NormalizeConfig(BaseModel):
    """Normalization settings for string comparison."""
    
    lowercase: Literal[True] = Field(..., description="Lowercase strings before comparison")
    strip_whitespace: Literal[True] = Field(..., description="Strip whitespace before comparison")


class MetricArgs(BaseModel):
    """Arguments for the exact_match metric."""
    
    pred_path: str = Field(..., description="JSONPath into extracted output")
    ref_path: str = Field(..., description="JSONPath into case.reference")
    normalize: NormalizeConfig


class MetricConfig(BaseModel):
    """Metric configuration."""
    
    name: Literal["exact_match"] = Field(..., description="Metric name (must be exact_match in v1-min)")
    type: Literal["exact_match"] = Field(..., description="Metric type (must be exact_match in v1-min)")
    args: MetricArgs


class ScoringConfig(BaseModel):
    """Scoring configuration."""
    
    metrics: list[MetricConfig] = Field(
        ..., 
        min_length=1, 
        max_length=1,
        description="List of metrics (exactly one in v1-min)"
    )
    primary_metric: Literal["exact_match"] = Field(
        ..., 
        description="Primary metric name (must be exact_match in v1-min)"
    )
    
    @model_validator(mode="after")
    def validate_metric_matches_primary(self) -> "ScoringConfig":
        """Ensure metric name matches primary_metric."""
        if self.metrics[0].name != self.primary_metric:
            raise ValueError(
                f"Metric name '{self.metrics[0].name}' must match primary_metric '{self.primary_metric}'"
            )
        return self


class AggregateConfig(BaseModel):
    """Aggregation configuration."""
    
    name: str = Field(..., description="Name for the aggregated metric")
    type: Literal["mean"] = Field(..., description="Aggregation type (must be mean in v1-min)")
    metric: Literal["exact_match"] = Field(
        ..., 
        description="Metric to aggregate (must be exact_match in v1-min)"
    )


class ReportingConfig(BaseModel):
    """Reporting configuration."""
    
    aggregate: list[AggregateConfig] = Field(
        ..., 
        min_length=1, 
        max_length=1,
        description="List of aggregations (exactly one in v1-min)"
    )


# --- Main spec model ---


class BenchmarkSpec(BaseModel):
    """
    Benchmark specification for v1-min.
    
    A benchmark spec defines:
    - Where the dataset lives
    - How to build HTTP requests from dataset cases
    - How to extract predictions from HTTP responses
    - How to score deterministically
    - How to aggregate metrics
    """
    
    id: str = Field(..., description="Unique identifier for the benchmark")
    name: str = Field(..., description="Human-readable benchmark name")
    version: int | str = Field(..., description="Benchmark version")
    
    dataset: DatasetConfig
    contract: ContractConfig
    scoring: ScoringConfig
    reporting: ReportingConfig


# --- Loader ---


class SpecLoadError(Exception):
    """Raised when a benchmark spec cannot be loaded or validated."""
    pass


def load_spec(path: str | Path) -> BenchmarkSpec:
    """
    Load and validate a benchmark spec from a YAML or JSON file.
    
    Args:
        path: Path to the benchmark spec file (.yaml, .yml, or .json)
        
    Returns:
        Validated BenchmarkSpec object
        
    Raises:
        SpecLoadError: If the file cannot be read or the spec is invalid
    """
    path = Path(path)
    
    if not path.exists():
        raise SpecLoadError(f"Spec file not found: {path}")
    
    try:
        content = path.read_text(encoding="utf-8")
    except Exception as e:
        raise SpecLoadError(f"Failed to read spec file: {e}") from e
    
    # Parse YAML (also handles JSON since JSON is valid YAML)
    try:
        data = yaml.safe_load(content)
    except yaml.YAMLError as e:
        raise SpecLoadError(f"Failed to parse spec file: {e}") from e
    
    if data is None:
        raise SpecLoadError("Spec file is empty")
    
    if not isinstance(data, dict):
        raise SpecLoadError("Spec must be a YAML/JSON object")
    
    # Validate with Pydantic
    try:
        return BenchmarkSpec.model_validate(data)
    except Exception as e:
        raise SpecLoadError(f"Invalid spec: {e}") from e

