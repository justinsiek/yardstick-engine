"""Basic import tests to verify the package is correctly structured."""


def test_import_yardstick_engine():
    """Verify the main package can be imported."""
    import yardstick_engine
    
    assert yardstick_engine.__version__ == "0.1.0"


def test_import_cli():
    """Verify the CLI module can be imported."""
    from yardstick_engine import cli
    
    assert callable(cli.main)

