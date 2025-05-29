import sys
import os
import pytest

sys.path.append(os.path.abspath(os.path.join(
    os.path.dirname(__file__), '..', 'functions')))

# Try importing with full relative path
import importlib.util
spec = importlib.util.spec_from_file_location("commander_ev", os.path.join(os.path.dirname(__file__), '..', 'functions', 'commander_ev.py'))
commander_ev = importlib.util.module_from_spec(spec)
spec.loader.exec_module(commander_ev)

def test_calculate_ev_basic():
    # Example: test with a simple input
    result = commander_ev.calculate_ev([1, 2, 3, 4, 5])
    assert abs(result - 3.0) < 1e-6

def test_calculate_ev_empty():
    # Should handle empty input gracefully
    result = commander_ev.calculate_ev([])
    assert result == 0

def test_calculate_ev_file_not_found():
    # Should raise FileNotFoundError for non-existent set/precon
    with pytest.raises(FileNotFoundError):
        commander_ev.calculate_ev('FAKESET', 'FAKEPRECON')
