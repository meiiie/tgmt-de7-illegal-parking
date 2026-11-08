param(
    [string]$BuildRoot = "$env:LOCALAPPDATA/CurbBuild/cache",
    [switch]$SkipDependencies,
    [switch]$SkipInstaller
)
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
$product = Get-Content -LiteralPath "$PSScriptRoot/curb/product.json" -Raw | ConvertFrom-Json
$version = $product.version
.venv/Scripts/python.exe scripts/sync_version.py --check
if ($LASTEXITCODE) { throw 'Version metadata mismatch' }
$build = [IO.Path]::GetFullPath($BuildRoot)
$stage = Join-Path $build 'stage'
$downloads = Join-Path $build 'downloads'
$dist = Join-Path $build 'dist'
New-Item -ItemType Directory -Force -Path "$stage/runtime",$downloads,$dist | Out-Null

function Get-Artifact([string]$Url, [string]$Path) {
    if (-not (Test-Path -LiteralPath $Path)) { Invoke-WebRequest $Url -OutFile $Path }
}

Get-Artifact 'https://www.python.org/ftp/python/3.12.10/python-3.12.10-embed-amd64.zip' "$downloads/python.zip"
if (-not (Test-Path "$stage/runtime/python.exe")) {
    Expand-Archive -LiteralPath "$downloads/python.zip" -DestinationPath "$stage/runtime" -Force
}
if ((Get-AuthenticodeSignature "$stage/runtime/python.exe").Status -ne 'Valid') { throw 'Invalid Python signature' }
Get-Artifact 'https://api.nuget.org/v3-flatcontainer/microsoft.web.webview2/1.0.4314.35/microsoft.web.webview2.1.0.4314.35.nupkg' "$downloads/webview2.zip"
if (-not (Test-Path "$downloads/webview2/lib/net462")) { Expand-Archive -LiteralPath "$downloads/webview2.zip" -DestinationPath "$downloads/webview2" -Force }
Get-Artifact 'https://go.microsoft.com/fwlink/p/?LinkId=2124703' "$downloads/MicrosoftEdgeWebview2Setup.exe"
if ((Get-AuthenticodeSignature "$downloads/MicrosoftEdgeWebview2Setup.exe").Status -ne 'Valid') { throw 'Invalid WebView2 installer signature' }
Get-Artifact 'https://github.com/GyanD/codexffmpeg/releases/download/7.1.1/ffmpeg-7.1.1-essentials_build.zip' "$downloads/ffmpeg.zip"
if ((Get-FileHash "$downloads/ffmpeg.zip" -Algorithm SHA256).Hash -ne '04861D3339C5EBE38B56C19A15CF2C0CC97F5DE4FA8910E4D47E5E6404E4A2D4') { throw 'FFmpeg checksum mismatch' }
Get-Artifact 'https://codeload.github.com/FFmpeg/FFmpeg/tar.gz/db69d06eeeab4f46da15030a80d539efb4503ca8' "$downloads/FFmpeg-7.1.1-source.tar.gz"

if (-not $SkipDependencies) {
    $env:UV_CACHE_DIR = Join-Path $build 'cache'
    uv pip install --quiet --python .venv/Scripts/python.exe --target "$stage/runtime/Lib/site-packages" --index https://download.pytorch.org/whl/cpu --index-strategy unsafe-best-match -r desktop/requirements-lock.txt
    if ($LASTEXITCODE) { throw 'Desktop dependencies failed' }
}
npm --prefix web run build
if ($LASTEXITCODE) { throw 'Frontend build failed' }
.venv/Scripts/python.exe -X utf8 scripts/prepare_desktop.py $stage $downloads
if ($LASTEXITCODE) { throw 'Desktop staging failed' }
$compiler = "$env:WINDIR/Microsoft.NET/Framework64/v4.0.30319/csc.exe"
& $compiler /nologo /target:winexe /platform:x64 /optimize+ "/win32icon:$stage/curb.ico" "/out:$stage/Curb.exe" /reference:System.dll /reference:System.Core.dll /reference:System.Drawing.dll /reference:System.Windows.Forms.dll "/reference:$stage/Microsoft.Web.WebView2.Core.dll" "/reference:$stage/Microsoft.Web.WebView2.WinForms.dll" '.\desktop\Curb.cs' "$stage\BuildInfo.cs"
if ($LASTEXITCODE) { throw 'Desktop compilation failed' }
if (-not $SkipInstaller) {
    $installerBuild = Join-Path $build 'installer'
    New-Item -ItemType Directory -Force -Path $installerBuild | Out-Null
    $iscc = @("${env:ProgramFiles(x86)}/Inno Setup 6/ISCC.exe", "$env:ProgramFiles/Inno Setup 7/ISCC.exe", "$env:LOCALAPPDATA/Programs/Inno Setup 6/ISCC.exe") | Where-Object {Test-Path $_} | Select-Object -First 1
    if (-not $iscc) { throw 'Install Inno Setup 6.5+ or 7 from https://jrsoftware.org/isdl.php' }
    & $iscc /Qp "/DStage=$stage" "/DDist=$installerBuild" "/DDownloads=$downloads" "/DAppVersion=$version" desktop/Curb.iss
    if ($LASTEXITCODE) { throw 'Installer build failed' }
    & $compiler /nologo /target:winexe /platform:x64 /optimize+ "/win32icon:$stage/curb.ico" "/out:$dist/Curb-Setup-$version-x64.exe" /reference:System.dll /reference:System.Core.dll /reference:System.Windows.Forms.dll "/resource:$installerBuild/Curb-Package-$version-x64.exe,Curb.Payload.exe" '.\desktop\Setup.cs' "$stage\BuildInfo.cs"
    if ($LASTEXITCODE) { throw 'Quick Install launcher compilation failed' }
    Get-FileHash "$dist/Curb-Setup-$version-x64.exe" -Algorithm SHA256 | Format-List
}
Write-Output "Desktop: $stage/Curb.exe"
Write-Output "Installer: $dist/Curb-Setup-$version-x64.exe"
