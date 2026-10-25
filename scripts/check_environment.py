from __future__ import annotations

import importlib.util
import platform
import sys


def main() -> int:
    print(f"Python: {sys.version.split()[0]}")
    print(f"Platform: {platform.platform()}")
    if sys.version_info < (3, 11):
        print("ERROR: Python 3.11+ est recommandé.")
        return 1
    required = ["fastapi", "numpy", "soundfile", "scipy"]
    for name in required:
        print(f"{name}: {'installed' if importlib.util.find_spec(name) else 'missing'}")
    print(f"faster_whisper: {'installed' if importlib.util.find_spec('faster_whisper') else 'optional / missing'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

