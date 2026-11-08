"""Local release checks; never print potential secret values."""
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATTERNS = [
    r"gh[pousr]_[A-Za-z0-9]{30,255}",
    r"github_pat_[A-Za-z0-9_]{60,}",
    r"sk-(?:proj-)?[A-Za-z0-9_-]{32,}",
    r"hf_[A-Za-z0-9]{30,}",
    r"AKIA[0-9A-Z]{16}",
    r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
]


def main():
    output = subprocess.check_output(["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=ROOT)
    candidates = sorted(set(output.decode("utf-8").split("\0")) - {""})
    findings, oversized = [], []
    source_hashes = {}
    for name in candidates:
        path = ROOT / name
        if not path.is_file():
            continue
        if path.stat().st_size > 10 * 1024**2:
            oversized.append(name)
        if path.suffix.lower() in {".png", ".jpg", ".ico", ".bmp", ".woff", ".woff2"}:
            continue
        content = path.read_text(encoding="utf-8-sig", errors="replace")
        for pattern in PATTERNS:
            for match in re.finditer(pattern, content):
                findings.append({"file": name, "line": content[:match.start()].count("\n") + 1})
        if name.startswith(("curb/", "desktop/", "web/src/")):
            source_hashes[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    report = {"files_scanned": len(candidates), "potential_secrets": findings, "oversized_files": oversized, "source_sha256": source_hashes}
    destination = ROOT / "outputs/release-1.1.0/source-check.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("files_scanned", "potential_secrets", "oversized_files")}, ensure_ascii=False))
    if findings or oversized:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
