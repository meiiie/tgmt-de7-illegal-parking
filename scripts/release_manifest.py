import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--build-root", type=Path, required=True)
    args = parser.parse_args()
    product = json.loads((ROOT / "curb/product.json").read_text(encoding="utf-8"))
    version = product["version"]
    stage, dist = args.build_root / "stage", args.build_root / "dist"
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip():
        raise SystemExit("Commit the verified source tree before creating a release manifest")
    staged_product = json.loads((stage / "curb/product.json").read_text(encoding="utf-8"))
    if staged_product != product:
        raise SystemExit("Staged product metadata does not match the source tree; rebuild first")
    installer = dist / f"Curb-Setup-{version}-x64.exe"
    if not installer.is_file():
        raise SystemExit("Build installer first")
    shutil.copy2(stage / "application-source.zip", dist / f"Curb-{version}-source.zip")
    shutil.copy2(stage / "licenses/FFmpeg-7.1.1-source.tar.gz", dist)
    shutil.copy2(stage / "packages.json", dist / f"Curb-{version}-dependencies.json")
    names = [installer.name, f"Curb-{version}-source.zip", f"Curb-{version}-dependencies.json", "FFmpeg-7.1.1-source.tar.gz"]
    checksums = []
    for name in names:
        with (dist / name).open("rb") as stream:
            checksums.append({"name": name, "bytes": (dist / name).stat().st_size, "sha256": hashlib.file_digest(stream, "sha256").hexdigest()})
    manifest = {"product": product, "platform": "Windows x64", "runtime": "CPU", "signed": False, "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(), "assets": checksums}
    (dist / "release-manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    checksums.append({"name": "release-manifest.json", "sha256": hashlib.sha256((dist / "release-manifest.json").read_bytes()).hexdigest()})
    (dist / "SHA256SUMS.txt").write_text("".join(f'{entry["sha256"]}  {entry["name"]}\n' for entry in checksums), encoding="ascii")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
