import pytest
import unittest.mock as mock
from geemap.ai import run_ee_code

def test_run_ee_code_sandboxing():
    """Verify that arbitrary code execution is blocked by __builtins__ sandboxing."""
    malicious_code = "__import__('os').system('echo VULNERABLE')"
    
    # Normally this would execute without error if not sandboxed
    with pytest.raises(NameError) as excinfo:
        run_ee_code(malicious_code, ee=mock.Mock(), geemap_instance=mock.Mock())
    
    assert "name '__import__' is not defined" in str(excinfo.value)

def test_run_ee_code_safe_builtins():
    """Verify that safe builtins like len, print, list are still available."""
    safe_code = "my_list = list(range(5))\nx = len(my_list)\nprint(x)"
    
    try:
        run_ee_code(safe_code, ee=mock.Mock(), geemap_instance=mock.Mock())
    except Exception as e:
        pytest.fail(f"Safe code execution failed with {e}")
