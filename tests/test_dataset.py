"""Tests for dataset loading and validation."""

import pytest
from pathlib import Path

from engine.dataset import load_dataset_jsonl, Case, DatasetLoadError


# Path to fixture dataset
FIXTURE_DATASET = Path(__file__).parent.parent / "benchmarks" / "addition_qa_v1" / "dataset.jsonl"


class TestCase:
    """Tests for Case model."""
    
    def test_valid_case(self):
        """Create a valid case."""
        case = Case(
            id="test_001",
            input={"question": "What is 2+2?"},
            reference={"answer": "4"}
        )
        assert case.id == "test_001"
        assert case.input == {"question": "What is 2+2?"}
        assert case.reference == {"answer": "4"}
    
    def test_empty_input_rejected(self):
        """Reject case with empty input."""
        with pytest.raises(ValueError, match="input must be a non-empty"):
            Case(id="test", input={}, reference={"answer": "4"})
    
    def test_empty_reference_rejected(self):
        """Reject case with empty reference."""
        with pytest.raises(ValueError, match="reference must be a non-empty"):
            Case(id="test", input={"q": "?"}, reference={})
    
    def test_empty_id_rejected(self):
        """Reject case with empty id string."""
        with pytest.raises(ValueError):
            Case(id="", input={"q": "?"}, reference={"a": "!"})


class TestLoadDatasetJsonl:
    """Tests for load_dataset_jsonl function."""
    
    def test_load_fixture_dataset(self):
        """Load the fixture dataset successfully."""
        cases = load_dataset_jsonl(FIXTURE_DATASET)
        
        assert len(cases) == 10
        assert all(isinstance(c, Case) for c in cases)
    
    def test_fixture_case_ids_unique(self):
        """All case IDs in fixture are unique."""
        cases = load_dataset_jsonl(FIXTURE_DATASET)
        ids = [c.id for c in cases]
        
        assert len(ids) == len(set(ids))
    
    def test_fixture_first_case(self):
        """Verify first case content."""
        cases = load_dataset_jsonl(FIXTURE_DATASET)
        
        assert cases[0].id == "add_001"
        assert cases[0].input == {"question": "What is 2 + 2?"}
        assert cases[0].reference == {"answer": "4"}
    
    def test_file_not_found(self):
        """Raise DatasetLoadError for missing file."""
        with pytest.raises(DatasetLoadError, match="not found"):
            load_dataset_jsonl("nonexistent.jsonl")
    
    def test_empty_file(self, tmp_path):
        """Raise DatasetLoadError for empty file."""
        empty_file = tmp_path / "empty.jsonl"
        empty_file.write_text("")
        
        with pytest.raises(DatasetLoadError, match="empty"):
            load_dataset_jsonl(empty_file)
    
    def test_invalid_json(self, tmp_path):
        """Raise DatasetLoadError for invalid JSON."""
        bad_file = tmp_path / "bad.jsonl"
        bad_file.write_text('{"id": "test", invalid}')
        
        with pytest.raises(DatasetLoadError, match="Invalid JSON on line 1"):
            load_dataset_jsonl(bad_file)
    
    def test_missing_id(self, tmp_path):
        """Raise DatasetLoadError for missing id field."""
        bad_file = tmp_path / "no_id.jsonl"
        bad_file.write_text('{"input": {"q": "?"}, "reference": {"a": "!"}}')
        
        with pytest.raises(DatasetLoadError, match="Invalid case on line 1"):
            load_dataset_jsonl(bad_file)
    
    def test_missing_input(self, tmp_path):
        """Raise DatasetLoadError for missing input field."""
        bad_file = tmp_path / "no_input.jsonl"
        bad_file.write_text('{"id": "test", "reference": {"a": "!"}}')
        
        with pytest.raises(DatasetLoadError, match="Invalid case on line 1"):
            load_dataset_jsonl(bad_file)
    
    def test_missing_reference(self, tmp_path):
        """Raise DatasetLoadError for missing reference field."""
        bad_file = tmp_path / "no_ref.jsonl"
        bad_file.write_text('{"id": "test", "input": {"q": "?"}}')
        
        with pytest.raises(DatasetLoadError, match="Invalid case on line 1"):
            load_dataset_jsonl(bad_file)
    
    def test_duplicate_ids(self, tmp_path):
        """Raise DatasetLoadError for duplicate case IDs."""
        dup_file = tmp_path / "duplicates.jsonl"
        dup_file.write_text(
            '{"id": "test", "input": {"q": "1"}, "reference": {"a": "1"}}\n'
            '{"id": "test", "input": {"q": "2"}, "reference": {"a": "2"}}'
        )
        
        with pytest.raises(DatasetLoadError, match="Duplicate case ID 'test' on line 2"):
            load_dataset_jsonl(dup_file)
    
    def test_non_object_line(self, tmp_path):
        """Raise DatasetLoadError for non-object JSON."""
        bad_file = tmp_path / "array.jsonl"
        bad_file.write_text('["not", "an", "object"]')
        
        with pytest.raises(DatasetLoadError, match="must be a JSON object"):
            load_dataset_jsonl(bad_file)
    
    def test_skips_empty_lines(self, tmp_path):
        """Empty lines are skipped."""
        sparse_file = tmp_path / "sparse.jsonl"
        sparse_file.write_text(
            '{"id": "1", "input": {"q": "a"}, "reference": {"a": "a"}}\n'
            '\n'
            '{"id": "2", "input": {"q": "b"}, "reference": {"a": "b"}}\n'
        )
        
        cases = load_dataset_jsonl(sparse_file)
        assert len(cases) == 2
        assert cases[0].id == "1"
        assert cases[1].id == "2"
    
    def test_input_must_be_object(self, tmp_path):
        """Raise error if input is not an object."""
        bad_file = tmp_path / "string_input.jsonl"
        bad_file.write_text('{"id": "test", "input": "string", "reference": {"a": "b"}}')
        
        with pytest.raises(DatasetLoadError, match="Invalid case"):
            load_dataset_jsonl(bad_file)
    
    def test_reference_must_be_object(self, tmp_path):
        """Raise error if reference is not an object."""
        bad_file = tmp_path / "string_ref.jsonl"
        bad_file.write_text('{"id": "test", "input": {"q": "?"}, "reference": "string"}')
        
        with pytest.raises(DatasetLoadError, match="Invalid case"):
            load_dataset_jsonl(bad_file)

