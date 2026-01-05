"""
Benchmark runner orchestration for v1-min.

This module implements the run_benchmark function that ties together
all components: HTTP invocation, extraction, scoring, and aggregation.
"""

from collections import Counter
from datetime import datetime, timezone
from typing import Any

from engine.aggregation import aggregate_mean
from engine.dataset import Case
from engine.extraction import ExtractionError, extract_output
from engine.metrics import MetricError, score_exact_match
from engine.results import CaseResult, ErrorInfo, RunResult, SystemResult
from engine.spec import BenchmarkSpec
from engine.systems import InvokeError, SystemConfig, invoke_case

__all__ = [
    "run_benchmark",
]


def _run_case(
    case: Case,
    system: SystemConfig,
    spec: BenchmarkSpec,
) -> CaseResult:
    """
    Run a single case against a system.
    
    Returns a CaseResult with either:
    - extracted_output + metrics (success), or
    - error (failure)
    """
    # Step 1: Construct request body ($.input in v1-min)
    body: dict[str, Any] = case.input
    
    # Step 2: Invoke HTTP
    try:
        response_json = invoke_case(system, body)
    except InvokeError as e:
        return CaseResult(
            case_id=case.id,
            error=ErrorInfo(
                code=e.code,
                message=e.message,
                http_status=e.http_status,
            ),
        )
    
    # Step 3: Extract output using output_json_path
    output_json_path = spec.contract.response.output_json_path
    try:
        extracted_output = extract_output(response_json, output_json_path)
    except ExtractionError as e:
        return CaseResult(
            case_id=case.id,
            error=ErrorInfo(
                code=e.code,
                message=e.message,
            ),
        )
    
    # Step 4: Score with exact_match
    # Get the metric config (v1-min has exactly one metric: exact_match)
    metric_config = spec.scoring.metrics[0]
    pred_path = metric_config.args.pred_path
    ref_path = metric_config.args.ref_path
    strip_punctuation = metric_config.args.normalize.strip_punctuation
    
    try:
        exact_match = score_exact_match(
            extracted_output,
            case.reference,
            pred_path,
            ref_path,
            strip_punctuation,
        )
    except MetricError as e:
        return CaseResult(
            case_id=case.id,
            extracted_output=extracted_output,
            error=ErrorInfo(
                code=e.code,
                message=e.message,
            ),
        )
    
    # Success: return extracted output and metrics
    return CaseResult(
        case_id=case.id,
        extracted_output=extracted_output,
        metrics={metric_config.name: exact_match},
    )


def _run_system(
    cases: list[Case],
    system: SystemConfig,
    spec: BenchmarkSpec,
) -> SystemResult:
    """
    Run all cases against a single system.
    
    Returns a SystemResult with aggregated metrics and per-case results.
    """
    case_results: list[CaseResult] = []
    error_counter: Counter[str] = Counter()
    metric_values: list[bool] = []
    
    # Get metric and aggregate config from spec
    metric_name = spec.scoring.primary_metric
    aggregate_config = spec.reporting.aggregate[0]
    
    for case in cases:
        result = _run_case(case, system, spec)
        case_results.append(result)
        
        if result.error:
            error_counter[result.error.code] += 1
        elif result.metrics:
            # Collect metric values for aggregation
            metric_values.append(result.metrics[metric_name])
    
    # Aggregate: compute mean of metric values
    aggregate_value = aggregate_mean(metric_values)
    
    # Sort error_counts for deterministic output
    sorted_error_counts = dict(sorted(error_counter.items()))
    
    return SystemResult(
        system_name=system.name,
        primary_metric=metric_name,
        aggregates={aggregate_config.name: aggregate_value},
        case_results=case_results,
        error_counts=sorted_error_counts,
    )


def run_benchmark(
    spec: BenchmarkSpec,
    cases: list[Case],
    systems: list[SystemConfig],
) -> RunResult:
    """
    Run a benchmark against one or more systems.
    
    For each system, evaluates all cases and produces aggregated results.
    A single case failure does not abort the run.
    
    Args:
        spec: The benchmark specification
        cases: List of dataset cases to evaluate
        systems: List of systems to test
        
    Returns:
        RunResult with per-system results and per-case breakdown
    """
    started_at = datetime.now(timezone.utc)
    
    system_results: list[SystemResult] = []
    for system in systems:
        result = _run_system(cases, system, spec)
        system_results.append(result)
    
    finished_at = datetime.now(timezone.utc)
    
    return RunResult(
        benchmark_id=spec.id,
        benchmark_version=spec.version,
        dataset_path=spec.dataset.path,
        started_at=started_at,
        finished_at=finished_at,
        systems=system_results,
    )

