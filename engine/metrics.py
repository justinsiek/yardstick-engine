"""
Scoring metrics for v1-min.

This module provides deterministic scoring functions for benchmark evaluation.
In v1-min, only the exact_match metric is supported.
"""

from typing import Any

from engine.jsonpath import eval_jsonpath, JSONPathError

__all__ = [
    "score_exact_match",
    "MetricError",
]


class MetricError(Exception):
    """
    Raised when metric scoring fails.
    
    Attributes:
        code: Error code for categorization (always 'metric_failed' in v1-min)
        message: Human-readable error message
    """
    
    def __init__(self, message: str) -> None:
        self.code = "metric_failed"
        self.message = message
        super().__init__(f"{self.code}: {message}")


def _normalize(value: Any) -> str:
    """
    Normalize a value for comparison.
    
    Applies:
    - Convert to string
    - Lowercase
    - Strip whitespace
    
    Args:
        value: Any value to normalize
        
    Returns:
        Normalized string representation
    """
    return str(value).lower().strip()


def score_exact_match(
    extracted_output: Any,
    reference: dict[str, Any],
    pred_path: str,
    ref_path: str,
) -> bool:
    """
    Score using exact string match after normalization.
    
    This metric compares the predicted value (extracted from the system output)
    with the reference value (from the case) after normalizing both:
    - Convert to string
    - Lowercase
    - Strip whitespace
    
    Args:
        extracted_output: The output extracted from the system response
        reference: The reference object from the case (case.reference)
        pred_path: JSONPath to extract predicted value from extracted_output
        ref_path: JSONPath to extract reference value from reference
        
    Returns:
        True if normalized values match exactly, False otherwise
        
    Raises:
        MetricError: If pred_path or ref_path cannot be evaluated (code: 'metric_failed')
    
    Examples:
        >>> score_exact_match("4", {"answer": "4"}, "$", "$.answer")
        True
        
        >>> score_exact_match("  FOUR  ", {"answer": "four"}, "$", "$.answer")
        True  # After normalization: "four" == "four"
        
        >>> score_exact_match({"value": "4"}, {"answer": "4"}, "$.value", "$.answer")
        True
    """
    # Extract predicted value
    try:
        pred_value = eval_jsonpath(extracted_output, pred_path)
    except JSONPathError as e:
        raise MetricError(
            f"Failed to extract predicted value at '{pred_path}': {e}"
        ) from e
    
    # Extract reference value
    try:
        ref_value = eval_jsonpath(reference, ref_path)
    except JSONPathError as e:
        raise MetricError(
            f"Failed to extract reference value at '{ref_path}': {e}"
        ) from e
    
    # Normalize and compare
    normalized_pred = _normalize(pred_value)
    normalized_ref = _normalize(ref_value)
    
    return normalized_pred == normalized_ref

