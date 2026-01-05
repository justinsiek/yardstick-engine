"""Tests for minimal JSONPath evaluator."""

import pytest

from engine.jsonpath import eval_jsonpath, JSONPathError


class TestEvalJsonpath:
    """Tests for eval_jsonpath function."""
    
    # --- Valid paths ---
    
    def test_root_returns_object(self):
        """$ returns the entire object."""
        obj = {"a": 1, "b": 2}
        assert eval_jsonpath(obj, "$") == {"a": 1, "b": 2}
    
    def test_root_with_primitive(self):
        """$ works with primitive values."""
        assert eval_jsonpath("hello", "$") == "hello"
        assert eval_jsonpath(42, "$") == 42
        assert eval_jsonpath(None, "$") is None
    
    def test_single_field(self):
        """$.field returns the field value."""
        obj = {"name": "Alice", "age": 30}
        assert eval_jsonpath(obj, "$.name") == "Alice"
        assert eval_jsonpath(obj, "$.age") == 30
    
    def test_nested_fields(self):
        """$.a.b.c navigates nested objects."""
        obj = {"a": {"b": {"c": "deep"}}}
        assert eval_jsonpath(obj, "$.a") == {"b": {"c": "deep"}}
        assert eval_jsonpath(obj, "$.a.b") == {"c": "deep"}
        assert eval_jsonpath(obj, "$.a.b.c") == "deep"
    
    def test_field_with_underscore(self):
        """Field names can contain underscores."""
        obj = {"my_field": "value", "_private": "secret"}
        assert eval_jsonpath(obj, "$.my_field") == "value"
        assert eval_jsonpath(obj, "$._private") == "secret"
    
    def test_field_with_numbers(self):
        """Field names can contain numbers (not at start)."""
        obj = {"field1": "one", "field2": "two"}
        assert eval_jsonpath(obj, "$.field1") == "one"
        assert eval_jsonpath(obj, "$.field2") == "two"
    
    def test_null_value_in_path(self):
        """Null values can be returned."""
        obj = {"value": None}
        assert eval_jsonpath(obj, "$.value") is None
    
    def test_whitespace_trimmed(self):
        """Leading/trailing whitespace is trimmed."""
        obj = {"a": 1}
        assert eval_jsonpath(obj, "  $  ") == {"a": 1}
        assert eval_jsonpath(obj, "  $.a  ") == 1
    
    # --- Invalid path syntax ---
    
    def test_empty_path_rejected(self):
        """Empty path is rejected."""
        with pytest.raises(JSONPathError, match="cannot be empty"):
            eval_jsonpath({}, "")
    
    def test_missing_dollar_rejected(self):
        """Path without $ prefix is rejected."""
        with pytest.raises(JSONPathError, match="must start with"):
            eval_jsonpath({}, "a.b.c")
    
    def test_array_index_not_supported(self):
        """Array indexing is not supported in v1-min."""
        with pytest.raises(JSONPathError, match="Invalid JSONPath syntax"):
            eval_jsonpath({"items": [1, 2, 3]}, "$.items[0]")
    
    def test_wildcard_not_supported(self):
        """Wildcards are not supported in v1-min."""
        with pytest.raises(JSONPathError, match="Invalid JSONPath syntax"):
            eval_jsonpath({}, "$.*")
    
    def test_filter_not_supported(self):
        """Filters are not supported in v1-min."""
        with pytest.raises(JSONPathError, match="Invalid JSONPath syntax"):
            eval_jsonpath({}, "$[?(@.active)]")
    
    def test_field_starting_with_number_rejected(self):
        """Field names cannot start with a number."""
        with pytest.raises(JSONPathError, match="Invalid JSONPath syntax"):
            eval_jsonpath({"1field": "bad"}, "$.1field")
    
    def test_special_chars_in_field_rejected(self):
        """Special characters in field names are rejected."""
        with pytest.raises(JSONPathError, match="Invalid JSONPath syntax"):
            eval_jsonpath({"field-name": "bad"}, "$.field-name")
    
    def test_double_dot_rejected(self):
        """Double dots are rejected."""
        with pytest.raises(JSONPathError, match="Invalid JSONPath syntax"):
            eval_jsonpath({"a": {"b": 1}}, "$.a..b")
    
    def test_trailing_dot_rejected(self):
        """Trailing dot is rejected."""
        with pytest.raises(JSONPathError, match="Invalid JSONPath syntax"):
            eval_jsonpath({"a": 1}, "$.a.")
    
    def test_non_string_path_rejected(self):
        """Non-string path is rejected."""
        with pytest.raises(JSONPathError, match="must be a string"):
            eval_jsonpath({}, 123)
    
    # --- Path resolution errors ---
    
    def test_field_not_found(self):
        """Missing field raises error with path info."""
        obj = {"a": 1}
        with pytest.raises(JSONPathError, match="Field 'b' not found"):
            eval_jsonpath(obj, "$.b")
    
    def test_nested_field_not_found(self):
        """Missing nested field shows full path."""
        obj = {"a": {"b": 1}}
        with pytest.raises(JSONPathError, match="Field 'c' not found"):
            eval_jsonpath(obj, "$.a.c")
    
    def test_access_field_on_primitive(self):
        """Accessing field on non-object raises error."""
        obj = {"a": "string"}
        with pytest.raises(JSONPathError, match="non-object type 'str'"):
            eval_jsonpath(obj, "$.a.b")
    
    def test_access_field_on_list(self):
        """Accessing field on list raises error."""
        obj = {"items": [1, 2, 3]}
        with pytest.raises(JSONPathError, match="non-object type 'list'"):
            eval_jsonpath(obj, "$.items.length")
    
    def test_access_field_on_null(self):
        """Accessing field on null raises error."""
        obj = {"value": None}
        with pytest.raises(JSONPathError, match="null value"):
            eval_jsonpath(obj, "$.value.nested")
    
    # --- Integration with Case structure ---
    
    def test_case_input_extraction(self):
        """Extract input from case-like structure."""
        case = {
            "id": "test_001",
            "input": {"question": "What is 2+2?"},
            "reference": {"answer": "4"}
        }
        assert eval_jsonpath(case, "$.input") == {"question": "What is 2+2?"}
        assert eval_jsonpath(case, "$.reference.answer") == "4"

