param(
    [string]$Destination = "..\zorvan-release",
    [switch]$Clean
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$destRoot = (Resolve-Path (Join-Path $repoRoot $Destination) -ErrorAction SilentlyContinue)
if (-not $destRoot) {
    $destRoot = Join-Path $repoRoot $Destination
}

if ($Clean -and (Test-Path $destRoot)) {
    Write-Host "Cleaning existing export directory: $destRoot"
    Remove-Item -Recurse -Force $destRoot
}

if (-not (Test-Path $destRoot)) {
    New-Item -ItemType Directory -Path $destRoot | Out-Null
}

$includeDirs = @(
    "zorvan",
    "scripts",
    ".github",
    "docs"
)

$includeFiles = @(
    "README.md",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "LICENSE",
    "CODE_OF_CONDUCT.md",
    "SECURITY.md",
    "SUPPORT.md",
    "requirements.txt",
    "requirements_dev.txt",
    "requirements_gui.txt",
    "pytest.ini",
    "pyproject.toml",
    "setup.py",
    "run_new_ui.py",
    "PUBLISH_ZORVAN.md",
    "RELEASE_SCOPE_ZORVAN.md",
    "ZORVAN_RELEASE_PLAN.md"
)

$excludeDirNames = @("artifacts", "__pycache__", ".venv", ".venv_old", ".git")
$excludeFilePatterns = @("*.log", "*.dmp", "*.stackdump")

function Copy-DirectoryFiltered {
    param(
        [string]$SourceDir,
        [string]$TargetDir
    )

    Get-ChildItem -Path $SourceDir -Recurse -Force | ForEach-Object {
        $relative = $_.FullName.Substring($SourceDir.Length).TrimStart([char[]]@('\', '/'))
        if (-not $relative) {
            return
        }

        $segments = $relative -split "[\\/]"
        if ($segments | Where-Object { $excludeDirNames -contains $_ }) {
            return
        }

        if (-not $_.PSIsContainer) {
            foreach ($pattern in $excludeFilePatterns) {
                if ($_.Name -like $pattern) {
                    return
                }
            }
        }

        $targetPath = Join-Path $TargetDir $relative

        if ($_.PSIsContainer) {
            if (-not (Test-Path $targetPath)) {
                New-Item -ItemType Directory -Path $targetPath | Out-Null
            }
        }
        else {
            $targetParent = Split-Path -Parent $targetPath
            if (-not (Test-Path $targetParent)) {
                New-Item -ItemType Directory -Path $targetParent | Out-Null
            }
            Copy-Item -Path $_.FullName -Destination $targetPath -Force
        }
    }
}

Write-Host "Exporting curated Zorvan release tree"
Write-Host "Source: $repoRoot"
Write-Host "Destination: $destRoot"

foreach ($dir in $includeDirs) {
    $sourcePath = Join-Path $repoRoot $dir
    if (-not (Test-Path $sourcePath)) {
        Write-Warning "Skipping missing directory: $dir"
        continue
    }
    $targetPath = Join-Path $destRoot $dir
    if (-not (Test-Path $targetPath)) {
        New-Item -ItemType Directory -Path $targetPath | Out-Null
    }
    Copy-DirectoryFiltered -SourceDir $sourcePath -TargetDir $targetPath
}

foreach ($file in $includeFiles) {
    $sourcePath = Join-Path $repoRoot $file
    if (-not (Test-Path $sourcePath)) {
        Write-Warning "Skipping missing file: $file"
        continue
    }
    $targetPath = Join-Path $destRoot $file
    $targetParent = Split-Path -Parent $targetPath
    if (-not (Test-Path $targetParent)) {
        New-Item -ItemType Directory -Path $targetParent | Out-Null
    }
    Copy-Item -Path $sourcePath -Destination $targetPath -Force
}

Write-Host "Curated export completed."
Write-Host "Next steps:"
Write-Host "  1) cd $destRoot"
Write-Host "  2) git init"
Write-Host "  3) git add ."
Write-Host "  4) git commit -m \"Initial Zorvan v0.1.0\""
