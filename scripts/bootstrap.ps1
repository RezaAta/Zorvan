# Bootstrap script for Windows (PowerShell)
# Creates/activates a virtual environment, installs runtime and dev requirements and installs local package editable.

param(
    [switch]$InstallGui
)

$venvPath = ".venv"

Write-Host "Creating venv at $venvPath (if missing)"
if (-Not (Test-Path $venvPath)) {
    python -m venv $venvPath
}

Write-Host "Activating venv"
.\$venvPath\Scripts\Activate.ps1

Write-Host "Upgrading pip"
python -m pip install --upgrade pip

if (Test-Path "requirements.txt") {
    Write-Host "Installing requirements.txt"
    pip install -r requirements.txt
}

if (Test-Path "requirements_dev.txt") {
    Write-Host "Installing development requirements"
    pip install -r requirements_dev.txt
}

if ($InstallGui -and (Test-Path "requirements_gui.txt")) {
    Write-Host "Installing GUI requirements"
    pip install -r requirements_gui.txt
}

Write-Host "Installing package in editable mode"
pip install -e .

Write-Host "Bootstrap complete. Activate the venv using '.\\.venv\\Scripts\\Activate.ps1' and run tests with pytest."
