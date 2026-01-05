"""
Output extraction for v1-min.

This module provides functions to extract output from HTTP responses
using JSONPath expressions.
"""

from typing import Any

from engine.jsonpath import eval_jsonpath, JSONPathError

__all__ = [
    "extract_output",
    "ExtractionError",
]


class ExtractionError(Exception):
    """
    Raised when output extraction fails.
    
    Attributes:
        code: Error code for categorization (always 'output_extraction_failed' in v1-min)
        message: Human-readable error message
        path: The JSONPath that failed to extract
    """
    
    def __init__(self, message: str, path: str) -> None:
        self.code = "output_extraction_failed"
        self.message = message
        self.path = path
        super().__init__(f"{self.code}: {message}")


def extract_output(response_json: Any, output_json_path: str) -> Any:
    """
    Extract output from an HTTP response using a JSONPath expression.
    
    This function applies the output_json_path from the benchmark spec
    to extract the relevant output from the system's HTTP response.
    
    Args:
        response_json: Parsed JSON response from the system under test
        output_json_path: JSONPath expression to extract output (e.g., "$" or "$.answer")
        
    Returns:
        The extracted value at the specified path
        
    Raises:
        ExtractionError: If the path cannot be evaluated (with code 'output_extraction_failed')
    
    Examples:
        >>> extract_output({"answer": "4", "confidence": 0.9}, "$.answer")
        "4"
        
        >>> extract_output({"result": {"value": 42}}, "$.result.value")
        42
        
        >>> extract_output({"answer": "4"}, "$")
        {"answer": "4"}
    """
    try:
        return eval_jsonpath(response_json, output_json_path)
    except JSONPathError as e:
        raise ExtractionError(
            message=str(e),
            path=output_json_path,
        ) from e

