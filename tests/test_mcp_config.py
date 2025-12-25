import pytest
from exporter.mcp.config import MCPConfig

def test_mcp_config_initialization(tmp_path):
    # Setup: Create a dummy dpd.db file in tmp_path
    db_file = tmp_path / "dpd.db"
    db_file.touch()
    
    config = MCPConfig(base_dir=tmp_path)
    assert config.db_path == db_file
    assert config.db_path.exists()

def test_mcp_config_missing_db(tmp_path):
    # tmp_path has no dpd.db
    with pytest.raises(FileNotFoundError):
        MCPConfig(base_dir=tmp_path)
