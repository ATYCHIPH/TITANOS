# TITANOS EXE Builder
# This script bundles TITANOS into a single executable using PyInstaller.

Write-Host "--- TITANOS EXE Builder ---" -ForegroundColor Cyan

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
Push-Location $ProjectRoot

Write-Host "Cleaning previous builds..."
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }

Write-Host "Building executable (this may take a few minutes)..."
# Note: We include the 'ui' and 'titanos' folders as data.
# We use --collect-all for some complex packages if needed.
pyinstaller --onefile --name titanos `
    --add-data "ui;ui" `
    --collect-all pydantic_ai `
    --collect-all interpreter `
    --hidden-import "uvicorn.logging" `
    --hidden-import "uvicorn.loops" `
    --hidden-import "uvicorn.loops.auto" `
    --hidden-import "uvicorn.protocols" `
    --hidden-import "uvicorn.protocols.http" `
    --hidden-import "uvicorn.protocols.http.auto" `
    --hidden-import "uvicorn.protocols.websockets" `
    --hidden-import "uvicorn.protocols.websockets.auto" `
    --hidden-import "uvicorn.lifespan" `
    --hidden-import "uvicorn.lifespan.on" `
    titanos/__main__.py

Write-Host "--- Build Complete ---" -ForegroundColor Green
Write-Host "Executable located at: $(Join-Path $ProjectRoot 'dist\titanos.exe')"
Pop-Location
