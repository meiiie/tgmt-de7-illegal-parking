$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath (Split-Path -Parent $PSScriptRoot)
New-Item -ItemType Directory -Force -Path data | Out-Null
$curbDemo = Join-Path (Get-Location).Path 'data/gaithersburg_480p.webm'
if (-not (Test-Path -LiteralPath $curbDemo)) {
    Invoke-WebRequest -Uri 'https://upload.wikimedia.org/wikipedia/commons/transcoded/9/9b/MD-355_and_MD-124_Gaithersburg_MD_2022-07-30_11-07-03_1.webm/MD-355_and_MD-124_Gaithersburg_MD_2022-07-30_11-07-03_1.webm.480p.vp9.webm' -OutFile $curbDemo
}
if ((Get-FileHash -LiteralPath $curbDemo -Algorithm SHA256).Hash.ToLowerInvariant() -ne 'beec44107014ecb9f74d04da9813dcfdd1c78f7f785e1be9bdf2417608485272') { throw 'Hash video nguồn không khớp. Không tạo mẫu.' }
if (-not (Test-Path -LiteralPath data/gaithersburg_20s.mp4)) {
    & ffmpeg -hide_banner -loglevel error -ss 40 -i $curbDemo -t 20 -an -c:v libx264 -pix_fmt yuv420p -movflags +faststart data/gaithersburg_20s.mp4
    if ($LASTEXITCODE -ne 0) { throw 'Không tạo được clip mẫu.' }
}
Write-Host 'Video: G. Edward Johnson, Wikimedia Commons, CC BY 4.0. Xem docs/demo-video-source.md.'
