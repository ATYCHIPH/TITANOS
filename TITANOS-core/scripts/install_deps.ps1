# TITANOS Dependency Installer
# This script installs the required libraries for TITANOS-core and its source bodies.

Write-Host "--- TITANOS Dependency Setup ---" -ForegroundColor Cyan

# Ensure we are in a virtual environment or confirm global install
if ($null -eq $env:VIRTUAL_ENV) {
    Write-Warning "No virtual environment detected. It is highly recommended to use one."
    $Confirm = Read-Host "Proceed with global installation? [y/N]"
    if ($Confirm -ne "y") {
        Write-Host "Installation aborted."
        exit
    }
}

Write-Host "Installing core dependencies..."
pip install pydantic pydantic-ai fastapi uvicorn rich requests packaging pyinstaller pywebview python-dotenv

Write-Host "Installing source-hands (Open Interpreter) dependencies..."
pip install open-interpreter

Write-Host "Verifying installations..."
python -c "import pydantic; import pydantic_ai; import interpreter; print('Success: All major dependencies are importable.')"

Write-Host "--- Setup Complete ---" -ForegroundColor Green
