"""Basic import tests to verify the package is correctly structured."""


def test_import_engine():
    """Verify the main package can be imported."""
    import engine
    
    assert engine.__version__ == "0.1.0"


def test_import_cli():
    """Verify the CLI module can be imported."""
    from engine import cli
    
    assert callable(cli.main)

