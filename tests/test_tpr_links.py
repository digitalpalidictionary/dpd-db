import pytest
from db.models import SuttaInfo
from tools.cache_load import load_tpr_codes_set

def test_sutta_info_has_tpr():
    # Mocking some data for the test
    # We assume 'dn1' is in the tpr_codes.json (as verified earlier)
    # and 'nonexistent' is not.
    
    tpr_codes = load_tpr_codes_set()
    
    # Test case 1: Sutta exists in TPR (testing case insensitivity and dot handling)
    sutta_exists = SuttaInfo(cst_code="DN1.1")
    assert sutta_exists.has_tpr is True
    
    sutta_exists_no_dot = SuttaInfo(cst_code="dn1")
    assert sutta_exists_no_dot.has_tpr is True
    
    # Test case 2: Sutta does not exist in TPR
    sutta_missing = SuttaInfo(cst_code="nonexistent")
    assert sutta_missing.has_tpr is False

    # Test case 3: Empty cst_code
    sutta_empty = SuttaInfo(cst_code="")
    assert sutta_empty.has_tpr is False
