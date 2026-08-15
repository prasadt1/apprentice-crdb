from __future__ import annotations

import os
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent
# Editable/src layout: <repo>/src/apprentice_crdb → parents[1] is the repo.
# Lambda zip layout: /var/task/apprentice_crdb → parent is the task root (eval/ sits beside it).
if os.environ.get("APPRENTICE_REPO_ROOT"):
    REPO_ROOT = Path(os.environ["APPRENTICE_REPO_ROOT"])
elif (PACKAGE_DIR.parent / "eval").is_dir():
    REPO_ROOT = PACKAGE_DIR.parent
else:
    REPO_ROOT = PACKAGE_DIR.parents[1]
WAREHOUSE_SCHEMA = PACKAGE_DIR / "warehouse" / "schema.sql"
WAREHOUSE_SEED = PACKAGE_DIR / "warehouse" / "seed.sql"
MEMORY_SCHEMA = REPO_ROOT / "sql" / "001_memory.sql"
