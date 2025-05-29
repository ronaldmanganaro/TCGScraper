import sys
import os
import pytest

sys.path.append(os.path.abspath(os.path.join(
    os.path.dirname(__file__), '..', 'pages')))
from pages.Cloud_Control import trigger_price_check

def test_trigger_price_check(capsys):
    trigger_price_check()
    captured = capsys.readouterr()
    assert "Price check triggered" in captured.out
