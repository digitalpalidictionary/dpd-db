import pytest
from tools.cache_load import load_tpr_codes_set
from tools.paths import ProjectPaths

def test_load_tpr_codes_set():
    pth = ProjectPaths()
    if pth.tpr_codes_json_path.exists():
        tpr_codes = load_tpr_codes_set()
        assert isinstance(tpr_codes, set)
        assert len(tpr_codes) > 0
        assert "dn1" in tpr_codes
    else:
        pytest.skip("tpr_codes.json not found")
