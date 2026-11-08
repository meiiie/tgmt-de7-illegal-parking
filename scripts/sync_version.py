import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    product = json.loads((ROOT / "curb/product.json").read_text(encoding="utf-8"))
    version = product["version"]
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version):
        raise ValueError("Desktop version must be major.minor.patch")
    for name in ("web/package.json", "web/package-lock.json"):
        path = ROOT / name
        data = json.loads(path.read_text(encoding="utf-8"))
        valid = data["version"] == version
        if "packages" in data:
            valid = valid and data["packages"][""]["version"] == version
            data["packages"][""]["version"] = version
        data["version"] = version
        if args.check:
            if not valid:
                raise SystemExit(f"Version drift in {name}; run scripts/sync_version.py")
        else:
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Curb {version}: versions consistent")


if __name__ == "__main__":
    main()
