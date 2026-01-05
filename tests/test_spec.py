"""Tests for benchmark spec loading and validation."""

import pytest
from pathlib import Path

from engine.spec import load_spec, BenchmarkSpec, SpecLoadError


# Path to fixture benchmark
FIXTURE_SPEC = Path(__file__).parent.parent / "benchmarks" / "addition_qa_v1" / "benchmark.yaml"


class TestLoadSpec:
    """Tests for load_spec function."""
    
    def test_load_valid_spec(self):
        """Load the fixture benchmark spec successfully."""
        spec = load_spec(FIXTURE_SPEC)
        
        assert isinstance(spec, BenchmarkSpec)
        assert spec.id == "addition_qa_v1"
        assert spec.name == "Addition QA Benchmark"
        assert spec.version == 1
    
    def test_spec_dataset_config(self):
        """Verify dataset configuration is loaded correctly."""
        spec = load_spec(FIXTURE_SPEC)
        
        assert spec.dataset.path == "dataset.jsonl"
    
    def test_spec_contract_config(self):
        """Verify contract configuration is loaded correctly."""
        spec = load_spec(FIXTURE_SPEC)
        
        assert spec.contract.protocol == "http"
        assert spec.contract.request.method == "POST"
        assert spec.contract.request.body_json_path == "$.input"
        assert spec.contract.response.output_json_path == "$.answer"
    
    def test_spec_scoring_config(self):
        """Verify scoring configuration is loaded correctly."""
        spec = load_spec(FIXTURE_SPEC)
        
        assert spec.scoring.primary_metric == "exact_match"
        assert len(spec.scoring.metrics) == 1
        
        metric = spec.scoring.metrics[0]
        assert metric.name == "exact_match"
        assert metric.type == "exact_match"
        assert metric.args.pred_path == "$"
        assert metric.args.ref_path == "$.answer"
        assert metric.args.normalize.lowercase is True
        assert metric.args.normalize.strip_whitespace is True
    
    def test_spec_reporting_config(self):
        """Verify reporting configuration is loaded correctly."""
        spec = load_spec(FIXTURE_SPEC)
        
        assert len(spec.reporting.aggregate) == 1
        
        agg = spec.reporting.aggregate[0]
        assert agg.name == "exact_match_rate"
        assert agg.type == "mean"
        assert agg.metric == "exact_match"
    
    def test_file_not_found(self):
        """Raise SpecLoadError for missing file."""
        with pytest.raises(SpecLoadError, match="not found"):
            load_spec("nonexistent.yaml")
    
    def test_invalid_yaml(self, tmp_path):
        """Raise SpecLoadError for invalid YAML."""
        bad_file = tmp_path / "bad.yaml"
        bad_file.write_text("{ invalid yaml [")
        
        with pytest.raises(SpecLoadError, match="parse"):
            load_spec(bad_file)
    
    def test_empty_file(self, tmp_path):
        """Raise SpecLoadError for empty file."""
        empty_file = tmp_path / "empty.yaml"
        empty_file.write_text("")
        
        with pytest.raises(SpecLoadError, match="empty"):
            load_spec(empty_file)
    
    def test_missing_required_field(self, tmp_path):
        """Raise SpecLoadError when required field is missing."""
        incomplete = tmp_path / "incomplete.yaml"
        incomplete.write_text("id: test\nname: Test")
        
        with pytest.raises(SpecLoadError, match="Invalid spec"):
            load_spec(incomplete)
    
    def test_invalid_protocol(self, tmp_path):
        """Raise SpecLoadError for invalid protocol."""
        bad_spec = tmp_path / "bad_protocol.yaml"
        bad_spec.write_text("""
id: test
name: Test
version: 1
dataset:
  path: data.jsonl
contract:
  protocol: grpc
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
""")
        
        with pytest.raises(SpecLoadError, match="Invalid spec"):
            load_spec(bad_spec)
    
    def test_invalid_method(self, tmp_path):
        """Raise SpecLoadError for non-POST method."""
        bad_spec = tmp_path / "bad_method.yaml"
        bad_spec.write_text("""
id: test
name: Test
version: 1
dataset:
  path: data.jsonl
contract:
  protocol: http
  request:
    method: GET
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
""")
        
        with pytest.raises(SpecLoadError, match="Invalid spec"):
            load_spec(bad_spec)
    
    def test_load_json_spec(self, tmp_path):
        """Load a valid spec from JSON format."""
        json_spec = tmp_path / "spec.json"
        json_spec.write_text("""{
  "id": "json_test",
  "name": "JSON Test",
  "version": 1,
  "dataset": {"path": "data.jsonl"},
  "contract": {
    "protocol": "http",
    "request": {"method": "POST", "body_json_path": "$.input"},
    "response": {"output_json_path": "$"}
  },
  "scoring": {
    "metrics": [{
      "name": "exact_match",
      "type": "exact_match",
      "args": {
        "pred_path": "$",
        "ref_path": "$.answer",
        "normalize": {"lowercase": true, "strip_whitespace": true}
      }
    }],
    "primary_metric": "exact_match"
  },
  "reporting": {
    "aggregate": [{"name": "exact_match_rate", "type": "mean", "metric": "exact_match"}]
  }
}""")
        
        spec = load_spec(json_spec)
        assert spec.id == "json_test"
        assert spec.name == "JSON Test"
    
    def test_string_version(self, tmp_path):
        """Accept string version numbers."""
        spec_file = tmp_path / "string_version.yaml"
        spec_file.write_text("""
id: test
name: Test
version: "1.0.0"
dataset:
  path: data.jsonl
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
""")
        
        spec = load_spec(spec_file)
        assert spec.version == "1.0.0"

