from __future__ import annotations

from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent
REPO_ROOT = PACKAGE_DIR.parents[1]
WAREHOUSE_SCHEMA = PACKAGE_DIR / "warehouse" / "schema.sql"
WAREHOUSE_SEED = PACKAGE_DIR / "warehouse" / "seed.sql"
MEMORY_SCHEMA = REPO_ROOT / "sql" / "001_memory.sql"
