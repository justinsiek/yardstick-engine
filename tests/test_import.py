"""Basic import tests to verify the package is correctly structured."""


def test_import_engine():
    """Verify the main package can be imported."""
    import engine
    
    assert engine.__version__ == "0.1.0"


def test_import_spec_module():
    """Verify the spec module can be imported."""
    from engine import spec
    
    assert callable(spec.load_spec)
    assert spec.BenchmarkSpec is not None
    assert spec.SpecLoadError is not None


def test_top_level_exports():
    """Verify public API is exported from top-level package."""
    from engine import load_spec, BenchmarkSpec, SpecLoadError
    from engine import load_dataset_jsonl, Case, DatasetLoadError
    from engine import eval_jsonpath, JSONPathError
    from engine import extract_output, ExtractionError
    from engine import score_exact_match, MetricError
    from engine import aggregate_mean
    from engine import SystemConfig, invoke_case, InvokeError
    
    # Spec
    assert callable(load_spec)
    assert BenchmarkSpec is not None
    assert issubclass(SpecLoadError, Exception)
    
    # Dataset
    assert callable(load_dataset_jsonl)
    assert Case is not None
    assert issubclass(DatasetLoadError, Exception)
    
    # JSONPath
    assert callable(eval_jsonpath)
    assert issubclass(JSONPathError, Exception)
    
    # Extraction
    assert callable(extract_output)
    assert issubclass(ExtractionError, Exception)
    
    # Metrics
    assert callable(score_exact_match)
    assert issubclass(MetricError, Exception)
    
    # Aggregation
    assert callable(aggregate_mean)
    
    # Systems
    assert SystemConfig is not None
    assert callable(invoke_case)
    assert issubclass(InvokeError, Exception)
    
    # Results
    from engine import ErrorInfo, CaseResult, SystemResult, RunResult
    assert ErrorInfo is not None
    assert CaseResult is not None
    assert SystemResult is not None
    assert RunResult is not None
    
    # Runner
    from engine import run_benchmark
    assert callable(run_benchmark)


def test_import_dataset_module():
    """Verify the dataset module can be imported."""
    from engine import dataset
    
    assert callable(dataset.load_dataset_jsonl)
    assert dataset.Case is not None
    assert dataset.DatasetLoadError is not None


def test_import_jsonpath_module():
    """Verify the jsonpath module can be imported."""
    from engine import jsonpath
    
    assert callable(jsonpath.eval_jsonpath)
    assert jsonpath.JSONPathError is not None


def test_import_extraction_module():
    """Verify the extraction module can be imported."""
    from engine import extraction
    
    assert callable(extraction.extract_output)
    assert extraction.ExtractionError is not None


def test_import_metrics_module():
    """Verify the metrics module can be imported."""
    from engine import metrics
    
    assert callable(metrics.score_exact_match)
    assert metrics.MetricError is not None


def test_import_aggregation_module():
    """Verify the aggregation module can be imported."""
    from engine import aggregation
    
    assert callable(aggregation.aggregate_mean)


def test_import_systems_module():
    """Verify the systems module can be imported."""
    from engine import systems
    
    assert systems.SystemConfig is not None
    assert callable(systems.invoke_case)
    assert systems.InvokeError is not None


def test_import_results_module():
    """Verify the results module can be imported."""
    from engine import results
    
    assert results.ErrorInfo is not None
    assert results.CaseResult is not None
    assert results.SystemResult is not None
    assert results.RunResult is not None


def test_import_runner_module():
    """Verify the runner module can be imported."""
    from engine import runner
    
    assert callable(runner.run_benchmark)

