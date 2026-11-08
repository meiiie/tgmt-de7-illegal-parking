$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath (Split-Path -Parent $PSScriptRoot)
& .venv/Scripts/python.exe -X utf8 scripts/download_demo.py
if ($LASTEXITCODE -ne 0) { throw 'Demo download failed. Run again to resume.' }
Write-Host 'MERL Street Scene, CC BY-SA 4.0. See docs/demo-video-source.md.'
