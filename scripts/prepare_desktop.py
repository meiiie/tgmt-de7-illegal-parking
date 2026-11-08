import argparse
import importlib.metadata
import json
import shutil
import subprocess
import zipfile
from pathlib import Path

from brand_assets import export_brand

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", type=Path)
    parser.add_argument("downloads", type=Path)
    args = parser.parse_args()
    stage, downloads = args.stage.resolve(), args.downloads.resolve()
    stage.mkdir(parents=True, exist_ok=True)
    for folder in ("curb", "web/dist", "data"):
        target = (stage / folder).resolve()
        if not target.is_relative_to(stage) or target == stage:
            raise ValueError("Staging target is outside build directory")
        if target.exists():
            shutil.rmtree(target)
    for folder in ("curb", "web/dist"):
        shutil.copytree(ROOT / folder, stage / folder, dirs_exist_ok=True, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    (stage / "data").mkdir(exist_ok=True)
    demo = json.loads((ROOT / "curb/demo.json").read_text(encoding="utf-8"))
    shutil.copy2(ROOT / "data" / demo["filename"], stage / "data")
    for filename in ("yolo26s.pt", "yolo26n.pt"):
        shutil.copy2(ROOT / filename, stage / filename)
    shutil.copy2(ROOT / "desktop/Curb.exe.config", stage)
    (stage / "runtime/python312._pth").write_text("python312.zip\n.\nLib/site-packages\n..\nimport site\n", encoding="utf-8")
    (stage / "bin").mkdir(exist_ok=True)
    ffmpeg = downloads / "ffmpeg/ffmpeg-7.1.1-essentials_build/bin"
    if not ffmpeg.is_dir():
        with zipfile.ZipFile(downloads / "ffmpeg.zip") as archive:
            archive.extractall(downloads / "ffmpeg")
    for name in ("ffmpeg.exe", "ffprobe.exe"):
        shutil.copy2(ffmpeg / name, stage / "bin" / name)
    sdk = downloads / "webview2"
    for name in ("Microsoft.Web.WebView2.Core.dll", "Microsoft.Web.WebView2.WinForms.dll"):
        shutil.copy2(sdk / "lib/net462" / name, stage / name)
    shutil.copy2(sdk / "runtimes/win-x64/native/WebView2Loader.dll", stage)

    export_brand(stage)
    shutil.copy2(stage / "curb.png", ROOT / "desktop/curb.png")
    product = json.loads((ROOT / "curb/product.json").read_text(encoding="utf-8"))
    version = product["version"]
    (stage / "BuildInfo.cs").write_text(
        f'[assembly: System.Reflection.AssemblyVersion("{version}.0")]\n'
        f'[assembly: System.Reflection.AssemblyFileVersion("{version}.0")]\n'
        '[assembly: System.Reflection.AssemblyCompany("Meiiie")]\n'
        '[assembly: System.Reflection.AssemblyCopyright("Copyright 2026 Meiiie. AGPL-3.0.")]\n'
        f'static class BuildInfo {{ public const string Version = "{version}"; }}\n', encoding="utf-8")
    shutil.copy2(ROOT / "LICENSE", stage)
    shutil.copy2(ROOT / "CHANGELOG.md", stage)
    licenses = stage / "licenses"
    licenses.mkdir(exist_ok=True)
    shutil.copy2(stage / "runtime/LICENSE.txt", licenses / "Python.txt")
    shutil.copy2(sdk / "LICENSE.txt", licenses / "WebView2.txt")
    shutil.copy2(ROOT / "docs/demo-video-source.md", licenses / "demo-video.md")
    shutil.copy2(ROOT / "docs/legacy-demo-video-source.md", licenses / "legacy-demo-video.md")
    shutil.copy2(ROOT / "desktop/install-notes.txt", stage / "README.txt")
    shutil.copy2(ROOT / "desktop/THIRD-PARTY-NOTICES.md", stage)
    shutil.copy2(ffmpeg.parent / "LICENSE", licenses / "FFmpeg.txt")
    shutil.copy2(ffmpeg.parent / "README.txt", licenses / "FFmpeg-build.txt")
    shutil.copy2(downloads / "FFmpeg-7.1.1-source.tar.gz", licenses)
    (licenses / "ffmpeg-version.txt").write_text(subprocess.check_output([str(ffmpeg / "ffmpeg.exe"), "-version"], text=True), encoding="utf-8")
    for name in ("react", "react-dom", "lucide-react", "@fontsource/be-vietnam-pro"):
        directory = ROOT / "web/node_modules" / name
        for path in directory.glob("*LICENSE*"):
            target = licenses / "frontend" / name.replace("/", "_")
            target.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target / path.name)
    distributions = sorted(importlib.metadata.distributions(path=[str(stage / "runtime/Lib/site-packages")]), key=lambda d: d.metadata["Name"].lower())
    packages = [{"name": d.metadata["Name"], "version": d.version, "license": d.metadata.get("License-Expression") or d.metadata.get("License", "See bundled dist-info")} for d in distributions]
    (stage / "packages.json").write_text(json.dumps(packages, ensure_ascii=False, indent=2), encoding="utf-8")
    (ROOT / "desktop/requirements-lock.txt").write_text("\n".join(f'{d.metadata["Name"]}=={d.version}' for d in distributions) + "\n", encoding="utf-8")
    with zipfile.ZipFile(stage / "application-source.zip", "w", zipfile.ZIP_DEFLATED) as archive:
        for folder in ("curb", "web/src", "web/public", "desktop", "scripts", "tests", "docs"):
            for path in (ROOT / folder).rglob("*"):
                if path.is_file() and "__pycache__" not in path.parts:
                    archive.write(path, path.relative_to(ROOT))
        for name in ("README.md", "LICENSE", "CHANGELOG.md", "SUPPORT.md", "SECURITY.md", "build-desktop.ps1", "setup-curb.ps1", "run-curb.ps1", "requirements-test.txt", "requirements-demo.txt", "requirements-app.txt", "web/package.json", "web/package-lock.json", "web/tsconfig.json", "web/vite.config.ts", "web/index.html"):
            if (ROOT / name).is_file():
                archive.write(ROOT / name, name)
    print(json.dumps({"stage": str(stage), "packages": len(packages), "bytes": sum(p.stat().st_size for p in stage.rglob("*") if p.is_file())}))


if __name__ == "__main__":
    main()
