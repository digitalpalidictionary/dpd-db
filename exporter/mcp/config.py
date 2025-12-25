from pathlib import Path
from tools.paths import ProjectPaths


class MCPConfig:
    def __init__(self, base_dir: Path | None = None):
        self.paths = ProjectPaths(base_dir)
        self.db_path = self.paths.dpd_db_path

        # Ensure the database exists
        if not self.db_path.exists():
            raise FileNotFoundError(f"DPD database not found at {self.db_path}")


mcp_config = MCPConfig()
