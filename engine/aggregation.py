"""
Aggregation functions for v1-min.

This module provides functions to aggregate per-case metric values
into benchmark-level summary metrics.

In v1-min, only the mean aggregation is supported.
"""

__all__ = [
    "aggregate_mean",
]


def aggregate_mean(values: list[bool]) -> float:
    """
    Compute the mean of boolean metric values.
    
    Converts booleans to numeric values (True=1, False=0) and computes
    the arithmetic mean. This is used to compute metrics like exact_match_rate.
    
    Note: This function only receives values from cases that produced
    valid metric results. Cases with errors should be excluded before
    calling this function and counted separately.
    
    Args:
        values: List of boolean metric values (True/False)
        
    Returns:
        Mean as a float between 0.0 and 1.0.
        Returns 0.0 if the list is empty (no valid cases).
    
    Examples:
        >>> aggregate_mean([True, True, False])
        0.6666666666666666
        
        >>> aggregate_mean([True, True, True])
        1.0
        
        >>> aggregate_mean([False, False])
        0.0
        
        >>> aggregate_mean([])
        0.0
    """
    if not values:
        return 0.0
    
    # Python booleans are integers (True=1, False=0), so sum works directly
    return sum(values) / len(values)

