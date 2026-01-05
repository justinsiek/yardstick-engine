"""Basic import tests to verify the package is correctly structured."""


def test_import_engine():
    """Verify the main package can be imported."""
    import engine
    
    assert engine.__version__ == "0.1.0"


def test_import_cli():
    """Verify the CLI module can be imported."""
    from engine import cli
    
    assert callable(cli.main)


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

