"""Tests for aggregation functions."""

import pytest

from engine.aggregation import aggregate_mean


class TestAggregateMean:
    """Tests for aggregate_mean function."""
    
    # --- Basic functionality ---
    
    def test_all_true(self):
        """All True values return 1.0."""
        assert aggregate_mean([True, True, True]) == 1.0
    
    def test_all_false(self):
        """All False values return 0.0."""
        assert aggregate_mean([False, False, False]) == 0.0
    
    def test_mixed_values(self):
        """Mixed values return correct mean."""
        # 2 out of 3 = 0.666...
        result = aggregate_mean([True, True, False])
        assert abs(result - 2/3) < 1e-10
    
    def test_single_true(self):
        """Single True returns 1.0."""
        assert aggregate_mean([True]) == 1.0
    
    def test_single_false(self):
        """Single False returns 0.0."""
        assert aggregate_mean([False]) == 0.0
    
    def test_half_true(self):
        """Half True, half False returns 0.5."""
        assert aggregate_mean([True, False]) == 0.5
        assert aggregate_mean([True, True, False, False]) == 0.5
    
    # --- Edge cases ---
    
    def test_empty_list_returns_zero(self):
        """Empty list returns 0.0 (no valid cases)."""
        assert aggregate_mean([]) == 0.0
    
    def test_large_list(self):
        """Works with large lists."""
        # 100 True, 100 False = 0.5
        values = [True] * 100 + [False] * 100
        assert aggregate_mean(values) == 0.5
    
    def test_one_true_many_false(self):
        """One True among many False."""
        values = [True] + [False] * 9
        assert aggregate_mean(values) == 0.1
    
    def test_one_false_many_true(self):
        """One False among many True."""
        values = [False] + [True] * 9
        assert aggregate_mean(values) == 0.9
    
    # --- Precision ---
    
    def test_precision_third(self):
        """1/3 is represented correctly."""
        result = aggregate_mean([True, False, False])
        assert abs(result - 1/3) < 1e-10
    
    def test_precision_two_thirds(self):
        """2/3 is represented correctly."""
        result = aggregate_mean([True, True, False])
        assert abs(result - 2/3) < 1e-10
    
    # --- Return type ---
    
    def test_returns_float(self):
        """Always returns a float."""
        assert isinstance(aggregate_mean([True]), float)
        assert isinstance(aggregate_mean([False]), float)
        assert isinstance(aggregate_mean([]), float)
        assert isinstance(aggregate_mean([True, False]), float)

