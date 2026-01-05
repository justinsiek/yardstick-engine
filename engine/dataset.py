"""
Dataset and Case models for v1-min.

This module defines the Case model and provides functions to load
and validate datasets from JSONL files.
"""

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, model_validator

__all__ = [
    "Case",
    "load_dataset_jsonl",
    "DatasetLoadError",
]


class Case(BaseModel):
    """
    A single benchmark case.
    
    Each case represents one evaluation example with:
    - id: Unique identifier for the case
    - input: Structured JSON input provided to the system under test
    - reference: Structured JSON reference output used for scoring
    """
    
    id: str = Field(..., min_length=1, description="Unique identifier for the case")
    input: dict[str, Any] = Field(..., description="Structured input for the system under test")
    reference: dict[str, Any] = Field(..., description="Reference output for scoring")
    
    @model_validator(mode="after")
    def validate_non_empty(self) -> "Case":
        """Ensure input and reference are non-empty objects."""
        if not self.input:
            raise ValueError("input must be a non-empty object")
        if not self.reference:
            raise ValueError("reference must be a non-empty object")
        return self


class DatasetLoadError(Exception):
    """Raised when a dataset cannot be loaded or validated."""
    pass


def load_dataset_jsonl(path: str | Path) -> list[Case]:
    """
    Load and validate a dataset from a JSONL file.
    
    Each line in the file must be a valid JSON object with:
    - id (required, must be unique across all cases)
    - input (required, JSON object)
    - reference (required, JSON object)
    
    Args:
        path: Path to the JSONL dataset file
        
    Returns:
        List of validated Case objects
        
    Raises:
        DatasetLoadError: If the file cannot be read or cases are invalid
    """
    path = Path(path)
    
    if not path.exists():
        raise DatasetLoadError(f"Dataset file not found: {path}")
    
    try:
        content = path.read_text(encoding="utf-8")
    except Exception as e:
        raise DatasetLoadError(f"Failed to read dataset file: {e}") from e
    
    cases: list[Case] = []
    seen_ids: set[str] = set()
    
    lines = content.strip().split("\n")
    
    if not lines or (len(lines) == 1 and not lines[0].strip()):
        raise DatasetLoadError("Dataset file is empty")
    
    for line_num, line in enumerate(lines, start=1):
        line = line.strip()
        if not line:
            continue  # Skip empty lines
        
        # Parse JSON
        try:
            data = json.loads(line)
        except json.JSONDecodeError as e:
            raise DatasetLoadError(
                f"Invalid JSON on line {line_num}: {e}"
            ) from e
        
        if not isinstance(data, dict):
            raise DatasetLoadError(
                f"Line {line_num}: Each line must be a JSON object"
            )
        
        # Validate with Pydantic
        try:
            case = Case.model_validate(data)
        except Exception as e:
            raise DatasetLoadError(
                f"Invalid case on line {line_num}: {e}"
            ) from e
        
        # Check for duplicate IDs
        if case.id in seen_ids:
            raise DatasetLoadError(
                f"Duplicate case ID '{case.id}' on line {line_num}"
            )
        seen_ids.add(case.id)
        
        cases.append(case)
    
    if not cases:
        raise DatasetLoadError("Dataset contains no valid cases")
    
    return cases

