"""Initialize the local ClaimShield SQLite catalog with fictional demo records."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.main import DB_PATH  # noqa: E402
from backend.app.storage import initialize  # noqa: E402


def main() -> None:
    initialize(DB_PATH)
    print(f"ClaimShield demo data initialized: {DB_PATH}")
    print("Fictional catalog: 3 customers, 3 vehicles, 3 policies.")


if __name__ == "__main__":
    main()
