# PowerShell script to run local checks.
#   .\scripts\run_checks.ps1             core tests (Tests/core) - fast, safe default
#   .\scripts\run_checks.ps1 -All        full pytest suite (GUI tests may hang/crash on Windows without a display)
#   .\scripts\run_checks.ps1 -Precommit  pre-commit hooks on all files
#   .\scripts\run_checks.ps1 -Format     apply black + isort
param(
    [switch]$Precommit,
    [switch]$Tests,
    [switch]$All,
    [switch]$Format
)

if ($Precommit) {
    Write-Output "Running pre-commit hooks..."
    python -m pre_commit run --all-files
}

if ($Format) {
    Write-Output "Running code formatters (black/isort)..."
    python -m black .
    python -m isort .
}

if ($All) {
    Write-Output "Running full pytest suite (offscreen Qt)..."
    $env:QT_QPA_PLATFORM = "offscreen"
    python -m pytest -q
}
elseif ($Tests -or (-not $Precommit -and -not $Format)) {
    Write-Output "Running core tests..."
    python -m pytest -q Tests/core
}
