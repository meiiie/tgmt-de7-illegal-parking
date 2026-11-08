param([switch]$Cpu)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) { throw 'Cần uv trong PATH: https://docs.astral.sh/uv/getting-started/installation/' }
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) { throw 'Cần Node.js 22.12+ và npm trong PATH.' }
if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) { throw 'Cần FFmpeg trong PATH: https://ffmpeg.org/download.html' }
if (-not (Test-Path -LiteralPath '.venv/Scripts/python.exe')) {
    & uv venv --python 3.12 .venv
    if ($LASTEXITCODE -ne 0) { throw 'Không tạo được môi trường Python 3.12.' }
}
$curbIndex = if ($Cpu) { 'https://download.pytorch.org/whl/cpu' } else { 'https://download.pytorch.org/whl/cu126' }
& uv pip install --python .venv/Scripts/python.exe torch==2.11.0 torchvision==0.26.0 --index-url $curbIndex
if ($LASTEXITCODE -ne 0) { throw 'Không cài được PyTorch.' }
& uv pip install --python .venv/Scripts/python.exe -r requirements-app.txt
if ($LASTEXITCODE -ne 0) { throw 'Không cài được dependencies ứng dụng.' }
& npm --prefix web ci
if ($LASTEXITCODE -ne 0) { throw 'Không cài được frontend.' }
& npm --prefix web run build
if ($LASTEXITCODE -ne 0) { throw 'Không build được frontend.' }
$curbWeights = @{
    'yolo26s.pt' = '646f8bc3fe0a656803d95c294f7852321748cb29d13466a1af8862e2db384a1b';
    'yolo26n.pt' = '9b09cc8bf347f0fc8a5f7657480587f25db09b34bf33b0652110fb03a8ad4fef'
}
foreach ($curbModel in $curbWeights.Keys) {
    if (-not (Test-Path -LiteralPath $curbModel)) {
        $curbPartial = Join-Path $PSScriptRoot "$curbModel.part"
        Invoke-WebRequest -Uri "https://github.com/ultralytics/assets/releases/download/v8.4.0/$curbModel" -OutFile $curbPartial
        if ((Get-FileHash -LiteralPath $curbPartial -Algorithm SHA256).Hash.ToLowerInvariant() -ne $curbWeights[$curbModel]) { throw "Hash không khớp: $curbModel. Không sử dụng tệp tải về." }
        Move-Item -LiteralPath $curbPartial -Destination (Join-Path $PSScriptRoot $curbModel)
    }
}
& uv pip check --python .venv/Scripts/python.exe
if ($LASTEXITCODE -ne 0) { throw 'Dependencies chưa tương thích.' }
Write-Host 'Đã chuẩn bị Curb. Mở Start-Curb.cmd để sử dụng.'
