"""Tests for scoring metrics."""

import pytest

from engine.metrics import score_exact_match, MetricError


class TestScoreExactMatch:
    """Tests for score_exact_match function."""
    
    # --- Exact matches ---
    
    def test_simple_string_match(self):
        """Identical strings match."""
        assert score_exact_match("4", {"answer": "4"}, "$", "$.answer") is True
    
    def test_simple_string_mismatch(self):
        """Different strings don't match."""
        assert score_exact_match("5", {"answer": "4"}, "$", "$.answer") is False
    
    def test_number_match(self):
        """Numbers are converted to strings and compared."""
        assert score_exact_match(4, {"answer": 4}, "$", "$.answer") is True
        assert score_exact_match(4, {"answer": "4"}, "$", "$.answer") is True
        assert score_exact_match("4", {"answer": 4}, "$", "$.answer") is True
    
    def test_nested_extraction(self):
        """Values can be extracted from nested structures."""
        extracted = {"result": {"value": "42"}}
        reference = {"expected": {"answer": "42"}}
        assert score_exact_match(
            extracted, reference, "$.result.value", "$.expected.answer"
        ) is True
    
    # --- Normalization: lowercase ---
    
    def test_case_insensitive_match(self):
        """Comparison is case-insensitive."""
        assert score_exact_match("HELLO", {"answer": "hello"}, "$", "$.answer") is True
        assert score_exact_match("Hello", {"answer": "HELLO"}, "$", "$.answer") is True
        assert score_exact_match("HeLLo", {"answer": "hEllO"}, "$", "$.answer") is True
    
    def test_mixed_case_words(self):
        """Mixed case sentences match."""
        assert score_exact_match(
            "The Quick Brown Fox",
            {"answer": "the quick brown fox"},
            "$", "$.answer"
        ) is True
    
    # --- Normalization: strip whitespace ---
    
    def test_leading_whitespace_stripped(self):
        """Leading whitespace is ignored."""
        assert score_exact_match("  hello", {"answer": "hello"}, "$", "$.answer") is True
        assert score_exact_match("hello", {"answer": "  hello"}, "$", "$.answer") is True
    
    def test_trailing_whitespace_stripped(self):
        """Trailing whitespace is ignored."""
        assert score_exact_match("hello  ", {"answer": "hello"}, "$", "$.answer") is True
        assert score_exact_match("hello", {"answer": "hello  "}, "$", "$.answer") is True
    
    def test_both_sides_whitespace_stripped(self):
        """Whitespace on both sides is stripped."""
        assert score_exact_match("  hello  ", {"answer": "hello"}, "$", "$.answer") is True
        assert score_exact_match("hello", {"answer": "  hello  "}, "$", "$.answer") is True
    
    def test_internal_whitespace_preserved(self):
        """Internal whitespace is NOT stripped (only leading/trailing)."""
        assert score_exact_match(
            "hello world", {"answer": "hello world"}, "$", "$.answer"
        ) is True
        assert score_exact_match(
            "hello  world", {"answer": "hello world"}, "$", "$.answer"
        ) is False  # Double space vs single space
    
    # --- Combined normalization ---
    
    def test_case_and_whitespace_normalization(self):
        """Both case and whitespace normalization applied together."""
        assert score_exact_match(
            "  HELLO WORLD  ",
            {"answer": "hello world"},
            "$", "$.answer"
        ) is True
    
    # --- Different value types ---
    
    def test_boolean_values(self):
        """Booleans are converted to strings."""
        assert score_exact_match(True, {"answer": "True"}, "$", "$.answer") is True
        assert score_exact_match(False, {"answer": "False"}, "$", "$.answer") is True
        # Note: Python's str(True) = "True", str(False) = "False"
    
    def test_none_value(self):
        """None is converted to 'None' string."""
        assert score_exact_match(None, {"answer": "None"}, "$", "$.answer") is True
        assert score_exact_match(None, {"answer": "none"}, "$", "$.answer") is True  # lowercase
    
    def test_float_values(self):
        """Floats are converted to strings."""
        assert score_exact_match(3.14, {"answer": "3.14"}, "$", "$.answer") is True
    
    def test_list_value(self):
        """Lists are converted to string representation."""
        # This tests edge case - lists become their string repr
        result = score_exact_match([1, 2, 3], {"answer": "[1, 2, 3]"}, "$", "$.answer")
        assert result is True
    
    # --- Path extraction errors ---
    
    def test_pred_path_not_found(self):
        """Missing pred_path raises MetricError."""
        with pytest.raises(MetricError) as exc_info:
            score_exact_match({"a": 1}, {"answer": "1"}, "$.missing", "$.answer")
        
        assert exc_info.value.code == "metric_failed"
        assert "predicted value" in exc_info.value.message
        assert "$.missing" in exc_info.value.message
    
    def test_ref_path_not_found(self):
        """Missing ref_path raises MetricError."""
        with pytest.raises(MetricError) as exc_info:
            score_exact_match("1", {"a": 1}, "$", "$.missing")
        
        assert exc_info.value.code == "metric_failed"
        assert "reference value" in exc_info.value.message
        assert "$.missing" in exc_info.value.message
    
    def test_invalid_pred_path_syntax(self):
        """Invalid pred_path syntax raises MetricError."""
        with pytest.raises(MetricError) as exc_info:
            score_exact_match({"items": [1]}, {"answer": "1"}, "$.items[0]", "$.answer")
        
        assert exc_info.value.code == "metric_failed"
    
    def test_invalid_ref_path_syntax(self):
        """Invalid ref_path syntax raises MetricError."""
        with pytest.raises(MetricError) as exc_info:
            score_exact_match("1", {"items": [1]}, "$", "$.items[0]")
        
        assert exc_info.value.code == "metric_failed"
    
    def test_pred_path_on_primitive(self):
        """Accessing field on primitive raises MetricError."""
        with pytest.raises(MetricError) as exc_info:
            score_exact_match("string", {"answer": "1"}, "$.field", "$.answer")
        
        assert exc_info.value.code == "metric_failed"
    
    # --- Integration with benchmark case structure ---
    
    def test_typical_qa_case(self):
        """Typical QA case from the fixture."""
        # Simulating: extracted_output is "4", reference is {"answer": "4"}
        extracted = "4"
        reference = {"answer": "4"}
        assert score_exact_match(extracted, reference, "$", "$.answer") is True
    
    def test_typical_qa_case_with_nested_output(self):
        """QA case where output is nested."""
        extracted = {"result": "4"}
        reference = {"answer": "4"}
        assert score_exact_match(extracted, reference, "$.result", "$.answer") is True

