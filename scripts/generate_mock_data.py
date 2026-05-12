import json
from pathlib import Path

from app.core.config import get_settings


def main() -> None:
    settings = get_settings()
    path = settings.resolved_synthetic_dataset_path
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        print(f"mock dataset already exists: {path}")
        return
    path.write_text(json.dumps({"conversations": []}, indent=2), encoding="utf-8")
    print(f"created mock dataset shell: {path}")


if __name__ == "__main__":
    main()
