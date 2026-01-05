"""Tests for CLI commands."""

import json
from pathlib import Path

import pytest
from pytest_httpx import HTTPXMock

from engine.cli import main, cmd_validate, cmd_run, _parse_system
from engine.systems import SystemConfig


# --- Fixtures ---


@pytest.fixture
def valid_spec(tmp_path):
    """Create a valid benchmark spec."""
    spec_content = """
id: test_benchmark
name: Test Benchmark
version: 1

dataset:
  path: dataset.jsonl

contract:
  protocol: http
  request:
    method: POST
    body_json_path: "$.input"
  response:
    output_json_path: "$"

scoring:
  metrics:
    - name: exact_match
      type: exact_match
      args:
        pred_path: "$.answer"
        ref_path: "$.answer"
        normalize:
          lowercase: true
          strip_whitespace: true
  primary_metric: exact_match

reporting:
  aggregate:
    - name: exact_match_rate
      type: mean
      metric: exact_match
"""
    spec_file = tmp_path / "benchmark.yaml"
    spec_file.write_text(spec_content)
    return spec_file


@pytest.fixture
def valid_dataset(tmp_path):
    """Create a valid dataset."""
    dataset_content = (
        '{"id": "case_1", "input": {"question": "1+1"}, "reference": {"answer": "2"}}\n'
        '{"id": "case_2", "input": {"question": "2+2"}, "reference": {"answer": "4"}}\n'
    )
    dataset_file = tmp_path / "dataset.jsonl"
    dataset_file.write_text(dataset_content)
    return dataset_file


@pytest.fixture
def valid_benchmark(valid_spec, valid_dataset):
    """Create a valid benchmark with spec and dataset."""
    return valid_spec


class TestParseSystem:
    """Tests for system string parsing."""
    
    def test_valid_format(self):
        """Parse valid name=url format."""
        system = _parse_system("my_system=http://localhost:8000/api")
        assert system.name == "my_system"
        assert system.endpoint == "http://localhost:8000/api"
    
    def test_url_with_path(self):
        """Parse URL with path."""
        system = _parse_system("prod=https://api.example.com/v1/solve")
        assert system.name == "prod"
        assert system.endpoint == "https://api.example.com/v1/solve"
    
    def test_strips_whitespace(self):
        """Strips whitespace from name and URL."""
        system = _parse_system("  test  =  http://localhost:8000  ")
        assert system.name == "test"
        assert system.endpoint == "http://localhost:8000"
    
    def test_missing_equals(self):
        """Missing = raises ValueError."""
        with pytest.raises(ValueError, match="Invalid system format"):
            _parse_system("invalid_format")
    
    def test_empty_name(self):
        """Empty name raises ValueError."""
        with pytest.raises(ValueError, match="name cannot be empty"):
            _parse_system("=http://localhost:8000")
    
    def test_empty_url(self):
        """Empty URL raises ValueError."""
        with pytest.raises(ValueError, match="URL cannot be empty"):
            _parse_system("test=")
    
    def test_url_with_equals(self):
        """URL containing = is parsed correctly."""
        system = _parse_system("test=http://example.com?param=value")
        assert system.name == "test"
        assert system.endpoint == "http://example.com?param=value"


class TestCmdValidate:
    """Tests for validate command."""
    
    def test_valid_benchmark(self, valid_benchmark, capsys):
        """Valid benchmark passes validation."""
        import argparse
        args = argparse.Namespace(spec=str(valid_benchmark))
        
        result = cmd_validate(args)
        
        assert result == 0
        captured = capsys.readouterr()
        assert "valid" in captured.out.lower()
    
    def test_missing_spec(self, tmp_path, capsys):
        """Missing spec file fails."""
        import argparse
        args = argparse.Namespace(spec=str(tmp_path / "nonexistent.yaml"))
        
        result = cmd_validate(args)
        
        assert result == 1
        captured = capsys.readouterr()
        assert "error" in captured.err.lower()
    
    def test_invalid_spec(self, tmp_path, capsys):
        """Invalid spec fails."""
        import argparse
        spec_file = tmp_path / "bad.yaml"
        spec_file.write_text("id: test\n# missing required fields")
        args = argparse.Namespace(spec=str(spec_file))
        
        result = cmd_validate(args)
        
        assert result == 1
        captured = capsys.readouterr()
        assert "error" in captured.err.lower()
    
    def test_missing_dataset(self, tmp_path, capsys):
        """Missing dataset fails."""
        import argparse
        spec_content = """
id: test
name: Test
version: 1
dataset:
  path: nonexistent.jsonl
contract:
  protocol: http
  request:
    method: POST
    body_json_path: "$.input"
  response:
    output_json_path: "$"
scoring:
  metrics:
    - name: exact_match
      type: exact_match
      args:
        pred_path: "$"
        ref_path: "$.answer"
        normalize:
          lowercase: true
          strip_whitespace: true
  primary_metric: exact_match
reporting:
  aggregate:
    - name: exact_match_rate
      type: mean
      metric: exact_match
"""
        spec_file = tmp_path / "benchmark.yaml"
        spec_file.write_text(spec_content)
        args = argparse.Namespace(spec=str(spec_file))
        
        result = cmd_validate(args)
        
        assert result == 1
        captured = capsys.readouterr()
        assert "dataset" in captured.err.lower()


class TestCmdRun:
    """Tests for run command."""
    
    def test_successful_run(self, httpx_mock: HTTPXMock, valid_benchmark, capsys):
        """Successful run returns 0."""
        import argparse
        
        # Mock successful responses
        httpx_mock.add_response(json={"answer": "2"})
        httpx_mock.add_response(json={"answer": "4"})
        
        args = argparse.Namespace(
            spec=str(valid_benchmark),
            systems=["test=http://test.local/api"],
            out=None,
        )
        
        result = cmd_run(args)
        
        assert result == 0
        captured = capsys.readouterr()
        assert "exact_match_rate" in captured.out
    
    def test_run_with_errors_still_returns_zero(self, httpx_mock: HTTPXMock, valid_benchmark, capsys):
        """Run with some errors still returns 0."""
        import argparse
        
        # First case succeeds, second fails
        httpx_mock.add_response(json={"answer": "2"})
        httpx_mock.add_response(status_code=500)
        
        args = argparse.Namespace(
            spec=str(valid_benchmark),
            systems=["test=http://test.local/api"],
            out=None,
        )
        
        result = cmd_run(args)
        
        assert result == 0  # Still 0 per spec
        captured = capsys.readouterr()
        assert "error" in captured.out.lower()
    
    def test_run_writes_output(self, httpx_mock: HTTPXMock, valid_benchmark, tmp_path, capsys):
        """Run writes results to output file."""
        import argparse
        
        httpx_mock.add_response(json={"answer": "2"})
        httpx_mock.add_response(json={"answer": "4"})
        
        out_file = tmp_path / "results.json"
        args = argparse.Namespace(
            spec=str(valid_benchmark),
            systems=["test=http://test.local/api"],
            out=str(out_file),
        )
        
        result = cmd_run(args)
        
        assert result == 0
        assert out_file.exists()
        
        # Verify JSON is valid
        results = json.loads(out_file.read_text())
        assert results["benchmark_id"] == "test_benchmark"
        assert "systems" in results
    
    def test_run_creates_output_directory(self, httpx_mock: HTTPXMock, valid_benchmark, tmp_path):
        """Run creates output directory if needed."""
        import argparse
        
        httpx_mock.add_response(json={"answer": "2"})
        httpx_mock.add_response(json={"answer": "4"})
        
        out_file = tmp_path / "subdir" / "results.json"
        args = argparse.Namespace(
            spec=str(valid_benchmark),
            systems=["test=http://test.local/api"],
            out=str(out_file),
        )
        
        result = cmd_run(args)
        
        assert result == 0
        assert out_file.exists()
    
    def test_run_no_systems(self, valid_benchmark, capsys):
        """Run without systems fails."""
        import argparse
        
        args = argparse.Namespace(
            spec=str(valid_benchmark),
            systems=None,
            out=None,
        )
        
        result = cmd_run(args)
        
        assert result == 1
        captured = capsys.readouterr()
        assert "system" in captured.err.lower()
    
    def test_run_invalid_system_format(self, valid_benchmark, capsys):
        """Run with invalid system format fails."""
        import argparse
        
        args = argparse.Namespace(
            spec=str(valid_benchmark),
            systems=["invalid_no_equals"],
            out=None,
        )
        
        result = cmd_run(args)
        
        assert result == 1
        captured = capsys.readouterr()
        assert "error" in captured.err.lower()
    
    def test_run_multiple_systems(self, httpx_mock: HTTPXMock, valid_benchmark, capsys):
        """Run with multiple systems."""
        import argparse
        
        # System 1 responses
        httpx_mock.add_response(json={"answer": "2"}, url="http://sys1.local/api")
        httpx_mock.add_response(json={"answer": "4"}, url="http://sys1.local/api")
        
        # System 2 responses  
        httpx_mock.add_response(json={"answer": "wrong"}, url="http://sys2.local/api")
        httpx_mock.add_response(json={"answer": "wrong"}, url="http://sys2.local/api")
        
        args = argparse.Namespace(
            spec=str(valid_benchmark),
            systems=["sys1=http://sys1.local/api", "sys2=http://sys2.local/api"],
            out=None,
        )
        
        result = cmd_run(args)
        
        assert result == 0
        captured = capsys.readouterr()
        assert "sys1" in captured.out
        assert "sys2" in captured.out


class TestMain:
    """Tests for main entrypoint."""
    
    def test_no_command_prints_help(self, capsys, monkeypatch):
        """No command prints help."""
        monkeypatch.setattr("sys.argv", ["yardstick"])
        
        result = main()
        
        assert result == 0
        captured = capsys.readouterr()
        assert "usage" in captured.out.lower() or "help" in captured.out.lower()
    
    def test_validate_command(self, valid_benchmark, monkeypatch, capsys):
        """Validate command works via main."""
        monkeypatch.setattr("sys.argv", ["yardstick", "validate", str(valid_benchmark)])
        
        result = main()
        
        assert result == 0

