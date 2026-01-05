"""Tests for benchmark runner orchestration."""

from datetime import datetime, timezone

import httpx
import pytest
from pytest_httpx import HTTPXMock

from engine.dataset import Case
from engine.results import CaseResult, ErrorInfo, RunResult, SystemResult
from engine.runner import run_benchmark
from engine.spec import load_spec
from engine.systems import SystemConfig


# --- Fixtures ---


@pytest.fixture
def simple_spec(tmp_path):
    """Create a simple benchmark spec for testing."""
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
    return load_spec(spec_file)


@pytest.fixture
def simple_cases():
    """Create simple test cases."""
    return [
        Case(id="case_1", input={"question": "1+1"}, reference={"answer": "2"}),
        Case(id="case_2", input={"question": "2+2"}, reference={"answer": "4"}),
        Case(id="case_3", input={"question": "3+3"}, reference={"answer": "6"}),
    ]


@pytest.fixture
def system():
    """Create a test system."""
    return SystemConfig(name="test_system", endpoint="http://test.local/solve")


class TestRunBenchmark:
    """Tests for run_benchmark function."""
    
    # --- Successful runs ---
    
    def test_all_cases_correct(self, httpx_mock: HTTPXMock, simple_spec, simple_cases, system):
        """All cases return correct answers."""
        # Mock responses for each case
        httpx_mock.add_response(json={"answer": "2"})
        httpx_mock.add_response(json={"answer": "4"})
        httpx_mock.add_response(json={"answer": "6"})
        
        result = run_benchmark(simple_spec, simple_cases, [system])
        
        assert result.benchmark_id == "test_benchmark"
        assert result.benchmark_version == 1
        assert len(result.systems) == 1
        
        sys_result = result.systems[0]
        assert sys_result.system_name == "test_system"
        assert sys_result.aggregates["exact_match_rate"] == 1.0
        assert sys_result.error_counts == {}
        assert len(sys_result.case_results) == 3
        
        for case_result in sys_result.case_results:
            assert case_result.error is None
            assert case_result.metrics == {"exact_match": True}
    
    def test_some_cases_wrong(self, httpx_mock: HTTPXMock, simple_spec, simple_cases, system):
        """Some cases return wrong answers."""
        httpx_mock.add_response(json={"answer": "2"})   # Correct
        httpx_mock.add_response(json={"answer": "5"})   # Wrong (should be 4)
        httpx_mock.add_response(json={"answer": "6"})   # Correct
        
        result = run_benchmark(simple_spec, simple_cases, [system])
        
        sys_result = result.systems[0]
        assert sys_result.aggregates["exact_match_rate"] == pytest.approx(2/3)
        
        # Check individual results
        assert sys_result.case_results[0].metrics == {"exact_match": True}
        assert sys_result.case_results[1].metrics == {"exact_match": False}
        assert sys_result.case_results[2].metrics == {"exact_match": True}
    
    def test_all_cases_wrong(self, httpx_mock: HTTPXMock, simple_spec, simple_cases, system):
        """All cases return wrong answers."""
        httpx_mock.add_response(json={"answer": "wrong"})
        httpx_mock.add_response(json={"answer": "wrong"})
        httpx_mock.add_response(json={"answer": "wrong"})
        
        result = run_benchmark(simple_spec, simple_cases, [system])
        
        sys_result = result.systems[0]
        assert sys_result.aggregates["exact_match_rate"] == 0.0
        
        for case_result in sys_result.case_results:
            assert case_result.metrics == {"exact_match": False}
    
    # --- Multiple systems ---
    
    def test_multiple_systems(self, httpx_mock: HTTPXMock, simple_spec, simple_cases):
        """Run against multiple systems."""
        system1 = SystemConfig(name="good_system", endpoint="http://good.local/solve")
        system2 = SystemConfig(name="bad_system", endpoint="http://bad.local/solve")
        
        # Good system - all correct
        httpx_mock.add_response(json={"answer": "2"}, url="http://good.local/solve")
        httpx_mock.add_response(json={"answer": "4"}, url="http://good.local/solve")
        httpx_mock.add_response(json={"answer": "6"}, url="http://good.local/solve")
        
        # Bad system - all wrong
        httpx_mock.add_response(json={"answer": "x"}, url="http://bad.local/solve")
        httpx_mock.add_response(json={"answer": "x"}, url="http://bad.local/solve")
        httpx_mock.add_response(json={"answer": "x"}, url="http://bad.local/solve")
        
        result = run_benchmark(simple_spec, simple_cases, [system1, system2])
        
        assert len(result.systems) == 2
        
        good_result = result.systems[0]
        assert good_result.system_name == "good_system"
        assert good_result.aggregates["exact_match_rate"] == 1.0
        
        bad_result = result.systems[1]
        assert bad_result.system_name == "bad_system"
        assert bad_result.aggregates["exact_match_rate"] == 0.0
    
    # --- Error handling ---
    
    def test_http_error_does_not_abort(self, httpx_mock: HTTPXMock, simple_spec, simple_cases, system):
        """HTTP error on one case does not abort the run."""
        httpx_mock.add_response(json={"answer": "2"})
        httpx_mock.add_response(status_code=500)  # Error
        httpx_mock.add_response(json={"answer": "6"})
        
        result = run_benchmark(simple_spec, simple_cases, [system])
        
        sys_result = result.systems[0]
        # 2 successful, 1 error -> rate is 2/2 = 1.0 (errors excluded from denominator)
        assert sys_result.aggregates["exact_match_rate"] == 1.0
        assert sys_result.error_counts == {"http_error": 1}
        
        assert sys_result.case_results[0].error is None
        assert sys_result.case_results[1].error is not None
        assert sys_result.case_results[1].error.code == "http_error"
        assert sys_result.case_results[2].error is None
    
    def test_invalid_json_error(self, httpx_mock: HTTPXMock, simple_spec, simple_cases, system):
        """Invalid JSON response produces error."""
        httpx_mock.add_response(json={"answer": "2"})
        httpx_mock.add_response(text="not json")  # Invalid JSON
        httpx_mock.add_response(json={"answer": "6"})
        
        result = run_benchmark(simple_spec, simple_cases, [system])
        
        sys_result = result.systems[0]
        assert sys_result.error_counts == {"invalid_json": 1}
        assert sys_result.case_results[1].error.code == "invalid_json"
    
    def test_extraction_error(self, httpx_mock: HTTPXMock, simple_spec, simple_cases, system):
        """Extraction failure produces error."""
        httpx_mock.add_response(json={"answer": "2"})
        httpx_mock.add_response(json={"wrong_field": "4"})  # Missing "answer" field
        httpx_mock.add_response(json={"answer": "6"})
        
        result = run_benchmark(simple_spec, simple_cases, [system])
        
        sys_result = result.systems[0]
        # metric_failed because pred_path $.answer fails on response
        assert "metric_failed" in sys_result.error_counts
        
        error_case = sys_result.case_results[1]
        assert error_case.error is not None
        assert error_case.error.code == "metric_failed"
        # extracted_output should still be captured
        assert error_case.extracted_output == {"wrong_field": "4"}
    
    def test_timeout_error(self, httpx_mock: HTTPXMock, simple_spec, simple_cases, system):
        """Timeout produces error."""
        httpx_mock.add_response(json={"answer": "2"})
        httpx_mock.add_exception(httpx.TimeoutException("Timeout"))
        httpx_mock.add_response(json={"answer": "6"})
        
        result = run_benchmark(simple_spec, simple_cases, [system])
        
        sys_result = result.systems[0]
        assert sys_result.error_counts == {"timeout": 1}
        assert sys_result.case_results[1].error.code == "timeout"
    
    def test_multiple_error_types(self, httpx_mock: HTTPXMock, simple_spec, system):
        """Multiple error types are counted separately."""
        cases = [
            Case(id="c1", input={"q": "1"}, reference={"answer": "1"}),
            Case(id="c2", input={"q": "2"}, reference={"answer": "2"}),
            Case(id="c3", input={"q": "3"}, reference={"answer": "3"}),
            Case(id="c4", input={"q": "4"}, reference={"answer": "4"}),
        ]
        
        httpx_mock.add_response(status_code=500)  # http_error
        httpx_mock.add_response(text="not json")  # invalid_json
        httpx_mock.add_exception(httpx.TimeoutException("Timeout"))  # timeout
        httpx_mock.add_response(json={"answer": "4"})  # success
        
        result = run_benchmark(simple_spec, cases, [system])
        
        sys_result = result.systems[0]
        assert sys_result.error_counts == {
            "http_error": 1,
            "invalid_json": 1,
            "timeout": 1,
        }
        assert sys_result.aggregates["exact_match_rate"] == 1.0  # 1/1 successful
    
    # --- Result structure ---
    
    def test_result_has_timestamps(self, httpx_mock: HTTPXMock, simple_spec, simple_cases, system):
        """Result includes start and finish timestamps."""
        httpx_mock.add_response(json={"answer": "2"})
        httpx_mock.add_response(json={"answer": "4"})
        httpx_mock.add_response(json={"answer": "6"})
        
        before = datetime.now(timezone.utc)
        result = run_benchmark(simple_spec, simple_cases, [system])
        after = datetime.now(timezone.utc)
        
        assert before <= result.started_at <= result.finished_at <= after
    
    def test_result_has_benchmark_info(self, httpx_mock: HTTPXMock, simple_spec, simple_cases, system):
        """Result includes benchmark metadata."""
        httpx_mock.add_response(json={"answer": "2"})
        httpx_mock.add_response(json={"answer": "4"})
        httpx_mock.add_response(json={"answer": "6"})
        
        result = run_benchmark(simple_spec, simple_cases, [system])
        
        assert result.benchmark_id == "test_benchmark"
        assert result.benchmark_version == 1
        assert result.dataset_path == "dataset.jsonl"
    
    def test_case_results_preserve_order(self, httpx_mock: HTTPXMock, simple_spec, simple_cases, system):
        """Case results maintain the order of input cases."""
        httpx_mock.add_response(json={"answer": "2"})
        httpx_mock.add_response(json={"answer": "4"})
        httpx_mock.add_response(json={"answer": "6"})
        
        result = run_benchmark(simple_spec, simple_cases, [system])
        
        case_ids = [cr.case_id for cr in result.systems[0].case_results]
        assert case_ids == ["case_1", "case_2", "case_3"]
    
    def test_extracted_output_captured(self, httpx_mock: HTTPXMock, simple_spec, simple_cases, system):
        """Extracted output is captured in result."""
        httpx_mock.add_response(json={"answer": "2", "extra": "data"})
        httpx_mock.add_response(json={"answer": "4"})
        httpx_mock.add_response(json={"answer": "6"})
        
        result = run_benchmark(simple_spec, simple_cases, [system])
        
        # output_json_path is "$" so full response is captured
        assert result.systems[0].case_results[0].extracted_output == {"answer": "2", "extra": "data"}
    
    def test_primary_metric_in_result(self, httpx_mock: HTTPXMock, simple_spec, simple_cases, system):
        """Primary metric is included in system result."""
        httpx_mock.add_response(json={"answer": "2"})
        httpx_mock.add_response(json={"answer": "4"})
        httpx_mock.add_response(json={"answer": "6"})
        
        result = run_benchmark(simple_spec, simple_cases, [system])
        
        assert result.systems[0].primary_metric == "exact_match"
    
    # --- Edge cases ---
    
    def test_empty_cases_list(self, httpx_mock: HTTPXMock, simple_spec, system):
        """Empty cases list produces valid result."""
        result = run_benchmark(simple_spec, [], [system])
        
        sys_result = result.systems[0]
        assert sys_result.aggregates["exact_match_rate"] == 0.0
        assert sys_result.case_results == []
        assert sys_result.error_counts == {}
    
    def test_single_case(self, httpx_mock: HTTPXMock, simple_spec, system):
        """Single case produces valid result."""
        cases = [Case(id="only", input={"q": "1"}, reference={"answer": "2"})]
        httpx_mock.add_response(json={"answer": "2"})
        
        result = run_benchmark(simple_spec, cases, [system])
        
        sys_result = result.systems[0]
        assert sys_result.aggregates["exact_match_rate"] == 1.0
        assert len(sys_result.case_results) == 1


class TestResultModels:
    """Tests for result model structures."""
    
    def test_error_info_model(self):
        """ErrorInfo model works correctly."""
        error = ErrorInfo(code="http_error", message="Server error", http_status=500)
        assert error.code == "http_error"
        assert error.message == "Server error"
        assert error.http_status == 500
    
    def test_error_info_without_status(self):
        """ErrorInfo without http_status."""
        error = ErrorInfo(code="timeout", message="Request timed out")
        assert error.http_status is None
    
    def test_case_result_success(self):
        """CaseResult for successful case."""
        result = CaseResult(
            case_id="test",
            extracted_output={"answer": "42"},
            metrics={"exact_match": True},
        )
        assert result.error is None
        assert result.metrics == {"exact_match": True}
    
    def test_case_result_error(self):
        """CaseResult for failed case."""
        result = CaseResult(
            case_id="test",
            error=ErrorInfo(code="timeout", message="Timed out"),
        )
        assert result.metrics is None
        assert result.extracted_output is None
    
    def test_run_result_serialization(self, httpx_mock: HTTPXMock, simple_spec, simple_cases, system):
        """RunResult can be serialized to JSON."""
        httpx_mock.add_response(json={"answer": "2"})
        httpx_mock.add_response(json={"answer": "4"})
        httpx_mock.add_response(json={"answer": "6"})
        
        result = run_benchmark(simple_spec, simple_cases, [system])
        
        # Should not raise
        json_str = result.model_dump_json()
        assert "test_benchmark" in json_str
        assert "exact_match_rate" in json_str

