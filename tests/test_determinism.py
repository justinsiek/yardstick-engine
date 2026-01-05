"""Tests for deterministic output."""

import json

import pytest
from pytest_httpx import HTTPXMock

from engine.dataset import Case
from engine.runner import run_benchmark
from engine.spec import load_spec
from engine.systems import SystemConfig


@pytest.fixture
def benchmark_spec(tmp_path):
    """Create a benchmark spec."""
    spec_content = """
id: determinism_test
name: Determinism Test
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
    return load_spec(spec_file)


@pytest.fixture
def test_cases():
    """Create test cases with stable ordering."""
    return [
        Case(id="case_a", input={"q": "1"}, reference={"answer": "1"}),
        Case(id="case_b", input={"q": "2"}, reference={"answer": "2"}),
        Case(id="case_c", input={"q": "3"}, reference={"answer": "3"}),
        Case(id="case_d", input={"q": "4"}, reference={"answer": "4"}),
        Case(id="case_e", input={"q": "5"}, reference={"answer": "5"}),
    ]


def _normalize_result(result_json: str) -> dict:
    """
    Normalize a result for comparison by removing timestamps.
    
    Returns a dict with timestamps replaced with placeholders.
    """
    data = json.loads(result_json)
    data["started_at"] = "TIMESTAMP"
    data["finished_at"] = "TIMESTAMP"
    return data


class TestDeterminism:
    """Tests for deterministic output."""
    
    def test_identical_runs_produce_identical_results(
        self, httpx_mock: HTTPXMock, benchmark_spec, test_cases
    ):
        """Two identical runs produce identical results (except timestamps)."""
        system = SystemConfig(name="test", endpoint="http://test.local/api")
        
        # Add responses for both runs (10 total = 5 cases x 2 runs)
        for _ in range(2):
            for case in test_cases:
                httpx_mock.add_response(json={"answer": case.reference["answer"]})
        
        # Run 1
        result1 = run_benchmark(benchmark_spec, test_cases, [system])
        
        # Run 2
        result2 = run_benchmark(benchmark_spec, test_cases, [system])
        
        # Compare normalized results
        norm1 = _normalize_result(result1.model_dump_json())
        norm2 = _normalize_result(result2.model_dump_json())
        
        assert norm1 == norm2
    
    def test_case_order_preserved(
        self, httpx_mock: HTTPXMock, benchmark_spec, test_cases
    ):
        """Case results maintain input order."""
        system = SystemConfig(name="test", endpoint="http://test.local/api")
        
        for case in test_cases:
            httpx_mock.add_response(json={"answer": case.reference["answer"]})
        
        result = run_benchmark(benchmark_spec, test_cases, [system])
        
        result_case_ids = [cr.case_id for cr in result.systems[0].case_results]
        input_case_ids = [c.id for c in test_cases]
        
        assert result_case_ids == input_case_ids
    
    def test_system_order_preserved(
        self, httpx_mock: HTTPXMock, benchmark_spec, test_cases
    ):
        """System results maintain input order."""
        systems = [
            SystemConfig(name="alpha", endpoint="http://alpha.local/api"),
            SystemConfig(name="beta", endpoint="http://beta.local/api"),
            SystemConfig(name="gamma", endpoint="http://gamma.local/api"),
        ]
        
        # Add responses for all systems
        for _ in systems:
            for case in test_cases:
                httpx_mock.add_response(json={"answer": case.reference["answer"]})
        
        result = run_benchmark(benchmark_spec, test_cases, systems)
        
        result_system_names = [sr.system_name for sr in result.systems]
        input_system_names = [s.name for s in systems]
        
        assert result_system_names == input_system_names
    
    def test_error_counts_sorted(
        self, httpx_mock: HTTPXMock, benchmark_spec
    ):
        """Error counts are sorted alphabetically by error code."""
        cases = [
            Case(id="c1", input={"q": "1"}, reference={"answer": "1"}),
            Case(id="c2", input={"q": "2"}, reference={"answer": "2"}),
            Case(id="c3", input={"q": "3"}, reference={"answer": "3"}),
        ]
        system = SystemConfig(name="test", endpoint="http://test.local/api")
        
        # Produce errors in non-alphabetical order: timeout, http_error, invalid_json
        import httpx
        httpx_mock.add_exception(httpx.TimeoutException("timeout"))
        httpx_mock.add_response(status_code=500)
        httpx_mock.add_response(text="not json")
        
        result = run_benchmark(benchmark_spec, cases, [system])
        
        error_codes = list(result.systems[0].error_counts.keys())
        
        # Should be sorted alphabetically
        assert error_codes == sorted(error_codes)
        assert error_codes == ["http_error", "invalid_json", "timeout"]
    
    def test_no_secrets_in_output(
        self, httpx_mock: HTTPXMock, benchmark_spec, test_cases
    ):
        """Output JSON does not contain sensitive fields."""
        system = SystemConfig(name="test", endpoint="http://test.local/api")
        
        for case in test_cases:
            httpx_mock.add_response(json={"answer": case.reference["answer"]})
        
        result = run_benchmark(benchmark_spec, test_cases, [system])
        result_json = result.model_dump_json()
        
        # These fields should NOT appear in output
        forbidden_fields = [
            "headers",
            "authorization",
            "api_key",
            "token",
            "password",
            "secret",
            "raw_response",
            "raw_request",
        ]
        
        result_lower = result_json.lower()
        for field in forbidden_fields:
            assert field not in result_lower, f"Found forbidden field: {field}"
    
    def test_output_schema_matches_spec(
        self, httpx_mock: HTTPXMock, benchmark_spec, test_cases
    ):
        """Output JSON has exactly the expected fields per spec §8."""
        system = SystemConfig(name="test", endpoint="http://test.local/api")
        
        for case in test_cases:
            httpx_mock.add_response(json={"answer": case.reference["answer"]})
        
        result = run_benchmark(benchmark_spec, test_cases, [system])
        data = json.loads(result.model_dump_json())
        
        # RunResult fields
        assert set(data.keys()) == {
            "benchmark_id",
            "benchmark_version", 
            "dataset_path",
            "started_at",
            "finished_at",
            "systems",
        }
        
        # SystemResult fields
        sys_data = data["systems"][0]
        assert set(sys_data.keys()) == {
            "system_name",
            "primary_metric",
            "aggregates",
            "case_results",
            "error_counts",
        }
        
        # CaseResult fields (success case)
        case_data = sys_data["case_results"][0]
        assert set(case_data.keys()) == {
            "case_id",
            "extracted_output",
            "metrics",
            "error",
        }

