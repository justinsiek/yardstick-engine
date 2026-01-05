"""Tests for output extraction."""

import pytest

from engine.extraction import extract_output, ExtractionError


class TestExtractOutput:
    """Tests for extract_output function."""
    
    # --- Valid extractions ---
    
    def test_extract_full_response(self):
        """$ returns the entire response."""
        response = {"answer": "4", "confidence": 0.9}
        result = extract_output(response, "$")
        assert result == {"answer": "4", "confidence": 0.9}
    
    def test_extract_single_field(self):
        """$.field extracts a single field."""
        response = {"answer": "4", "confidence": 0.9}
        assert extract_output(response, "$.answer") == "4"
        assert extract_output(response, "$.confidence") == 0.9
    
    def test_extract_nested_field(self):
        """$.a.b.c extracts nested fields."""
        response = {"result": {"value": {"answer": "42"}}}
        assert extract_output(response, "$.result") == {"value": {"answer": "42"}}
        assert extract_output(response, "$.result.value") == {"answer": "42"}
        assert extract_output(response, "$.result.value.answer") == "42"
    
    def test_extract_null_value(self):
        """Null values can be extracted."""
        response = {"answer": None}
        assert extract_output(response, "$.answer") is None
    
    def test_extract_various_types(self):
        """Various JSON types can be extracted."""
        response = {
            "string": "hello",
            "number": 42,
            "float": 3.14,
            "boolean": True,
            "array": [1, 2, 3],
            "object": {"nested": "value"}
        }
        assert extract_output(response, "$.string") == "hello"
        assert extract_output(response, "$.number") == 42
        assert extract_output(response, "$.float") == 3.14
        assert extract_output(response, "$.boolean") is True
        assert extract_output(response, "$.array") == [1, 2, 3]
        assert extract_output(response, "$.object") == {"nested": "value"}
    
    # --- Extraction errors ---
    
    def test_field_not_found_error(self):
        """Missing field raises ExtractionError."""
        response = {"answer": "4"}
        
        with pytest.raises(ExtractionError) as exc_info:
            extract_output(response, "$.missing")
        
        assert exc_info.value.code == "output_extraction_failed"
        assert exc_info.value.path == "$.missing"
        assert "not found" in exc_info.value.message
    
    def test_nested_field_not_found_error(self):
        """Missing nested field raises ExtractionError."""
        response = {"result": {"value": 42}}
        
        with pytest.raises(ExtractionError) as exc_info:
            extract_output(response, "$.result.missing")
        
        assert exc_info.value.code == "output_extraction_failed"
        assert exc_info.value.path == "$.result.missing"
    
    def test_invalid_path_syntax_error(self):
        """Invalid JSONPath syntax raises ExtractionError."""
        response = {"items": [1, 2, 3]}
        
        with pytest.raises(ExtractionError) as exc_info:
            extract_output(response, "$.items[0]")
        
        assert exc_info.value.code == "output_extraction_failed"
        assert "Invalid JSONPath" in exc_info.value.message
    
    def test_access_field_on_primitive_error(self):
        """Accessing field on primitive raises ExtractionError."""
        response = {"value": "string"}
        
        with pytest.raises(ExtractionError) as exc_info:
            extract_output(response, "$.value.nested")
        
        assert exc_info.value.code == "output_extraction_failed"
        assert "non-object" in exc_info.value.message
    
    def test_access_field_on_null_error(self):
        """Accessing field on null raises ExtractionError."""
        response = {"value": None}
        
        with pytest.raises(ExtractionError) as exc_info:
            extract_output(response, "$.value.nested")
        
        assert exc_info.value.code == "output_extraction_failed"
        assert "null" in exc_info.value.message
    
    # --- Error attributes ---
    
    def test_error_has_correct_code(self):
        """ExtractionError always has code 'output_extraction_failed'."""
        try:
            extract_output({}, "$.missing")
        except ExtractionError as e:
            assert e.code == "output_extraction_failed"
    
    def test_error_has_path(self):
        """ExtractionError includes the path that failed."""
        try:
            extract_output({}, "$.deep.nested.path")
        except ExtractionError as e:
            assert e.path == "$.deep.nested.path"
    
    def test_error_message_is_descriptive(self):
        """ExtractionError message is human-readable."""
        try:
            extract_output({"a": 1}, "$.b")
        except ExtractionError as e:
            assert "b" in e.message
            assert "not found" in e.message
    
    # --- Integration with typical response structures ---
    
    def test_openai_style_response(self):
        """Extract from OpenAI-style response structure."""
        response = {
            "choices": [
                {"message": {"content": "The answer is 4"}}
            ],
            "usage": {"tokens": 10}
        }
        # Note: array access not supported in v1-min, so we'd need $.choices
        result = extract_output(response, "$.choices")
        assert result == [{"message": {"content": "The answer is 4"}}]
    
    def test_simple_qa_response(self):
        """Extract from simple QA response."""
        response = {"answer": "4"}
        assert extract_output(response, "$.answer") == "4"

