param(
    [ValidateRange(1,65535)][int]$Port = 8765,
    [string]$DataDir = '',
    [switch]$Build,
    [switch]$NoBrowser
)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$curbPython = Join-Path $PSScriptRoot '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $curbPython)) {
    throw 'Chưa có môi trường Python. Chạy setup-curb.ps1 trước.'
}
if ($Build -or -not (Test-Path -LiteralPath 'web/dist/index.html')) {
    if (-not (Test-Path -LiteralPath 'web/node_modules')) {
        & npm --prefix web ci
        if ($LASTEXITCODE -ne 0) { throw 'Cài frontend không thành công.' }
    }
    & npm --prefix web run build
    if ($LASTEXITCODE -ne 0) { throw 'Build frontend không thành công.' }
}
if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
    throw 'Thiếu FFmpeg trong PATH. Xem README để cài đặt.'
}
$curbUrl = "http://127.0.0.1:$Port/"
$curbLive = $null
try {
    $curbRequest = [System.Net.HttpWebRequest]::Create("${curbUrl}api/health")
    $curbRequest.Proxy = $null
    $curbRequest.Timeout = 4000
    $curbResponse = $curbRequest.GetResponse()
    try {
        $curbReader = New-Object System.IO.StreamReader($curbResponse.GetResponseStream())
        try { $curbLive = $curbReader.ReadToEnd() | ConvertFrom-Json } finally { $curbReader.Dispose() }
    } finally { $curbResponse.Dispose() }
} catch { $curbLive = $null }
if ($curbLive -and $curbLive.local_only -and $curbLive.storage_path) {
    $curbExpected = if ($DataDir) { [System.IO.Path]::GetFullPath($DataDir) } elseif ($env:CURB_DATA_DIR) { [System.IO.Path]::GetFullPath($env:CURB_DATA_DIR) } else { Join-Path $PSScriptRoot 'outputs/curb' }
    if ([System.IO.Path]::GetFullPath($curbLive.storage_path) -ne [System.IO.Path]::GetFullPath($curbExpected)) {
        throw 'Cổng này đang phục vụ thư mục dữ liệu khác. Chọn cổng khác bằng -Port.'
    }
    Write-Host "Curb đang chạy: $curbUrl"
    if (-not $NoBrowser) { Start-Process $curbUrl }
    exit 0
}
$env:PYTHONUTF8 = '1'
$env:GRADIO_ANALYTICS_ENABLED = 'False'
$curbArguments = @('-X','utf8','-m','curb','--port',"$Port")
if ($DataDir) { $curbArguments += @('--data-dir',$DataDir) }
if (-not $NoBrowser) { $curbArguments += '--open' }
Write-Host "Curb: $curbUrl"
Write-Host 'Nhấn Ctrl+C để dừng ứng dụng. Mỗi thư mục dữ liệu chỉ mở một phiên.'
& $curbPython @curbArguments
exit $LASTEXITCODE
