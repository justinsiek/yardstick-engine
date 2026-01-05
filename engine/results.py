"""
Result models for v1-min.

This module defines the result schema for benchmark runs as specified
in §8 of the OSS Engine Spec.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

__all__ = [
    "ErrorInfo",
    "CaseResult",
    "SystemResult",
    "RunResult",
]


class ErrorInfo(BaseModel):
    """
    Structured error information for a failed case.
    
    Error codes (from spec §8):
    - timeout: Request timed out
    - http_error: Non-2xx HTTP status
    - invalid_json: Response is not valid JSON
    - output_extraction_failed: JSONPath extraction failed
    - metric_failed: Metric computation failed
    """
    
    code: str = Field(..., description="Error code identifying the failure type")
    message: str = Field(..., description="Human-readable error message")
    http_status: int | None = Field(
        default=None,
        description="HTTP status code (only for http_error)",
    )


class CaseResult(BaseModel):
    """
    Result for a single case evaluation.
    
    Each case produces either:
    - extracted_output + metrics (success), or
    - error with structured error info (failure)
    """
    
    case_id: str = Field(..., description="ID of the evaluated case")
    extracted_output: Any | None = Field(
        default=None,
        description="Extracted JSON object/value from response",
    )
    metrics: dict[str, bool] | None = Field(
        default=None,
        description="Metric results, e.g. {'exact_match': true}",
    )
    error: ErrorInfo | None = Field(
        default=None,
        description="Error info if case failed",
    )


class SystemResult(BaseModel):
    """
    Result for evaluating all cases against a single system.
    """
    
    system_name: str = Field(..., description="Name of the system under test")
    primary_metric: str = Field(..., description="Name of the primary metric")
    aggregates: dict[str, float] = Field(
        ...,
        description="Aggregated metrics, e.g. {'exact_match_rate': 0.8}",
    )
    case_results: list[CaseResult] = Field(
        ...,
        description="Per-case results",
    )
    error_counts: dict[str, int] = Field(
        ...,
        description="Count of errors by error code",
    )


class RunResult(BaseModel):
    """
    Complete result for a benchmark run.
    
    Contains per-system results and per-case breakdown.
    """
    
    benchmark_id: str = Field(..., description="ID from benchmark spec")
    benchmark_version: str | int = Field(..., description="Version from benchmark spec")
    dataset_path: str = Field(..., description="Path to the dataset file")
    started_at: datetime = Field(..., description="When the run started")
    finished_at: datetime = Field(..., description="When the run finished")
    systems: list[SystemResult] = Field(..., description="Per-system results")

