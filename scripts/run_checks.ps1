# PowerShell script to run basic checks locally
param(
    [switch]$precommit,
    [switch]$tests,
    [switch]$format
)

if ($precommit) {
    Write-Output "Running pre-commit hooks..."
    pre-commit run --all-files
}

if ($format) {
    Write-Output "Running code formatters (black/isort)..."
    black .
    isort .
}

if ($tests -or (-not $precommit -and -not $format)) {
    Write-Output "Running pytest..."
    pytest -q
}
