import sys
from unittest.mock import MagicMock, patch

# Mock local modules
sys.modules["db.db_helpers"] = MagicMock()
sys.modules["db.models"] = MagicMock()
sys.modules["audio.db.db_helpers"] = MagicMock()
sys.modules["exporter.webapp.preloads"] = MagicMock()
sys.modules["exporter.webapp.toolkit"] = MagicMock()
sys.modules["tools.css_manager"] = MagicMock()
sys.modules["tools.pali_text_files"] = MagicMock()
sys.modules["tools.tipitaka_db"] = MagicMock()
sys.modules["tools.translit"] = MagicMock()
sys.modules["sqlalchemy.orm"] = MagicMock()

# Mock ProjectPaths
with patch("tools.paths.ProjectPaths") as MockPaths:
    mock_paths = MockPaths.return_value
    mock_paths.webapp_static_dir = "static"
    mock_paths.webapp_templates_dir = "templates"
    mock_paths.webapp_css_path = "style.css"
    mock_paths.webapp_js_path = "script.js"
    mock_paths.webapp_home_simple_css_path = "simple.css"
    mock_paths.dpd_db_path = "dpd.db"

    # Mock open
    with patch("builtins.open", create=True) as mock_open:
        mock_open.return_value.__enter__.return_value.read.return_value = ""

        # Mock StaticFiles to avoid directory check
        with patch("fastapi.staticfiles.StaticFiles") as MockStaticFiles:
            
            # Import main
            from exporter.webapp.main import update_history

def test_memory_leak():
    # Simulate 1000 searches
    current_list = []
    for i in range(1000):
        current_list = update_history(f"search_{i}", "", "fuzzy")
        
    print(f"History size after 1000 unique searches: {len(current_list)}")
    
    assert len(current_list) <= 250, "History list grew beyond 250 items!"
