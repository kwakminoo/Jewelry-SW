$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $PSScriptRoot

$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $python)) {
    throw "가상환경이 없습니다. 먼저 'py -m venv .venv'를 실행하세요."
}

& $python -m pip install -r requirements.txt
& $python -m PyInstaller `
    --noconfirm `
    --clean `
    --windowed `
    --onefile `
    --name "Jewelry SW" `
    --collect-all PyQt6 `
    --add-data "jewelry\ui\resources;jewelry\ui\resources" `
    desktop_launcher.py

Write-Host ""
Write-Host "빌드 완료: dist\Jewelry SW.exe" -ForegroundColor Green
