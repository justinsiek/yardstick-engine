"""
System invocation for v1-min.

This module provides the SystemConfig model and functions to invoke
systems under test via HTTP.
"""

from typing import Any

import httpx
from pydantic import BaseModel, Field

__all__ = [
    "SystemConfig",
    "invoke_case",
    "InvokeError",
]


class SystemConfig(BaseModel):
    """
    Configuration for a system under test.
    
    A system is an HTTP endpoint that accepts JSON input and returns JSON output.
    In v1-min, only POST requests are supported with no headers or auth.
    """
    
    name: str = Field(..., min_length=1, description="Name identifier for the system")
    endpoint: str = Field(..., min_length=1, description="HTTP URL endpoint")


class InvokeError(Exception):
    """
    Raised when invoking a system fails.
    
    Attributes:
        code: Error code - one of: 'timeout', 'http_error', 'invalid_json'
        message: Human-readable error message
        http_status: HTTP status code (only for http_error), None otherwise
    """
    
    def __init__(self, code: str, message: str, http_status: int | None = None) -> None:
        self.code = code
        self.message = message
        self.http_status = http_status
        super().__init__(f"{code}: {message}")


# Default timeout in seconds
_DEFAULT_TIMEOUT = 30.0


def invoke_case(system: SystemConfig, body: dict[str, Any]) -> Any:
    """
    Invoke a system with a case input and return the parsed JSON response.
    
    Sends a POST request with JSON body to the system endpoint and parses
    the response as JSON.
    
    Args:
        system: The system configuration (name and endpoint)
        body: The JSON body to send (typically case.input)
        
    Returns:
        Parsed JSON response from the system
        
    Raises:
        InvokeError: If the request fails with one of these codes:
            - 'timeout': Request timed out
            - 'http_error': Non-2xx status code (includes http_status)
            - 'invalid_json': Response is not valid JSON
    """
    try:
        response = httpx.post(
            system.endpoint,
            json=body,
            timeout=_DEFAULT_TIMEOUT,
        )
    except httpx.TimeoutException as e:
        raise InvokeError(
            code="timeout",
            message=f"Request to {system.endpoint} timed out after {_DEFAULT_TIMEOUT}s",
        ) from e
    except httpx.RequestError as e:
        raise InvokeError(
            code="http_error",
            message=f"Request to {system.endpoint} failed: {e}",
        ) from e
    
    # Check for non-2xx status
    if not response.is_success:
        raise InvokeError(
            code="http_error",
            message=f"Request to {system.endpoint} returned status {response.status_code}",
            http_status=response.status_code,
        )
    
    # Parse JSON response
    try:
        return response.json()
    except Exception as e:
        raise InvokeError(
            code="invalid_json",
            message=f"Response from {system.endpoint} is not valid JSON: {e}",
        ) from e

