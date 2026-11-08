param([ValidateRange(1, 65535)][int]$Port = 7867)

$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$demoPython = Join-Path $PSScriptRoot '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $demoPython)) {
    throw 'Chua co moi truong .venv. Xem docs/local-smoke-2026-11-06.md.'
}
$env:PYTHONUTF8 = '1'
$env:GRADIO_ANALYTICS_ENABLED = 'False'
$env:GRADIO_TEMP_DIR = Join-Path $PSScriptRoot 'outputs/gradio-temp'
$env:YOLO_CONFIG_DIR = Join-Path $PSScriptRoot 'outputs/ultralytics-config'
& $demoPython -X utf8 -c "import app; app.build().queue().launch(server_name='127.0.0.1', server_port=$Port, allowed_paths=[app.RUNS])"
exit $LASTEXITCODE
