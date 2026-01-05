"""
Minimal JSONPath evaluator for v1-min.

This module provides a minimal JSONPath implementation supporting only:
- $ (root object)
- $.field (single field access)
- $.a.b.c (nested field access)

Not supported in v1-min:
- Array indexing ([0])
- Filters
- Unions
- Wildcards
"""

import re
from typing import Any

__all__ = [
    "eval_jsonpath",
    "JSONPathError",
]


class JSONPathError(Exception):
    """Raised when a JSONPath expression cannot be evaluated."""
    pass


# Pattern for valid v1-min JSONPath: $ or $.field.field.field...
# Field names can contain letters, numbers, underscores
_JSONPATH_PATTERN = re.compile(r'^\$(?:\.([a-zA-Z_][a-zA-Z0-9_]*))*$')


def eval_jsonpath(obj: Any, path: str) -> Any:
    """
    Evaluate a JSONPath expression against an object.
    
    Supports only v1-min JSONPath syntax:
    - $ : returns the root object
    - $.field : returns obj["field"]
    - $.a.b.c : returns obj["a"]["b"]["c"]
    
    Args:
        obj: The object to evaluate the path against
        path: A JSONPath expression (must start with $)
        
    Returns:
        The value at the specified path
        
    Raises:
        JSONPathError: If the path is invalid or cannot be resolved
    """
    if not isinstance(path, str):
        raise JSONPathError(f"JSONPath must be a string, got {type(path).__name__}")
    
    path = path.strip()
    
    if not path:
        raise JSONPathError("JSONPath cannot be empty")
    
    if not path.startswith("$"):
        raise JSONPathError(f"JSONPath must start with '$', got: {path}")
    
    # Validate path format
    if not _JSONPATH_PATTERN.match(path):
        raise JSONPathError(f"Invalid JSONPath syntax: {path}")
    
    # Handle root case
    if path == "$":
        return obj
    
    # Extract field names (skip the leading "$.")
    fields = path[2:].split(".")
    
    # Traverse the object
    current = obj
    traversed = "$"
    
    for field in fields:
        traversed = f"{traversed}.{field}"
        
        if current is None:
            raise JSONPathError(
                f"Cannot access '{field}' on null value at path: {traversed}"
            )
        
        if not isinstance(current, dict):
            raise JSONPathError(
                f"Cannot access '{field}' on non-object type '{type(current).__name__}' at path: {traversed}"
            )
        
        if field not in current:
            raise JSONPathError(
                f"Field '{field}' not found at path: {traversed}"
            )
        
        current = current[field]
    
    return current

