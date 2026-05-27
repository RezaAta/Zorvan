<#
.SYNOPSIS
Build a standalone Windows executable for Zorvan's GUI.
.DESCRIPTION
Uses PyInstaller to package run_new_ui.py and required GUI resource files into a single executable.
.EXAMPLE
.\scripts\build_exe.ps1
.EXAMPLE
.\scripts\build_exe.ps1 -PythonExe ".\.venv\Scripts\python.exe" -Name "ZorvanNewUI"
#>

[CmdletBinding()]
param(
    [string]$PythonExe = "python",
    [string]$Name = "ZorvanNewUI"
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Resolve-Path (Join-Path $scriptDir "..")
Set-Location $projectRoot

Write-Host "Building Windows executable for Zorvan in $projectRoot"
Write-Host "Using Python executable: $PythonExe"

$pythonCmd = Get-Command $PythonExe -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    throw "Python executable '$PythonExe' was not found. Activate your virtualenv or provide a valid path."
}

$pyInstallerArgs = @(
    "-m", "PyInstaller",
    "--noconfirm",
    "--clean",
    "--windowed",
    "--onefile",
    "--name", $Name,
    "--add-data", 'gui_framework\legacy\styles_template.qss;gui_framework\legacy',
    "--add-data", 'gui_framework\legacy\styles.qss;gui_framework\legacy',
    "--add-data", 'custom_nodes.json;.'
)

$iconPath = Join-Path $projectRoot "assets\zorvan.ico"
if (Test-Path $iconPath) {
    Write-Host "Using application icon: $iconPath"
    $pyInstallerArgs += "--icon"
    $pyInstallerArgs += $iconPath
    $pyInstallerArgs += "--add-data"
    $pyInstallerArgs += "assets\\zorvan.ico;assets"
} else {
    Write-Host "WARNING: assets\zorvan.ico not found. Building without the custom application icon."
}

# Collect node modules that are imported dynamically from the zorvan.Nodes package.
$pyInstallerArgs += "--collect-submodules"
$pyInstallerArgs += "zorvan.Nodes"
$pyInstallerArgs += "run_new_ui.py"

Write-Host "Running PyInstaller..."
& $PythonExe @pyInstallerArgs

if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller build failed with exit code $LASTEXITCODE."
}

Write-Host ""
Write-Host "Build complete."
Write-Host "Executable created in: $(Join-Path $projectRoot "dist\$Name.exe")"
