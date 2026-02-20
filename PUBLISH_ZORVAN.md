# Publish Zorvan (v0.1.0)

This repository is currently your development source (`MVVM-UI-Migration`).
Publish `Zorvan` using a curated export.

## 1) Create curated export

From repository root:

```powershell
./scripts/export_zorvan_release.ps1 -Destination "../zorvan-release" -Clean
```

## 2) Create GitHub repository

Create a new empty public repository named `zorvan` in your GitHub account/org.

- Do not initialize with README/license/gitignore (the export already contains these).
- Copy the repository URL (for example: `https://github.com/ORG_OR_USER/zorvan.git`).

## 3) Initialize and push

```powershell
cd ../zorvan-release
git init
git checkout -b main
git add .
git commit -m "Initial Zorvan v0.1.0"
git remote add origin https://github.com/ORG_OR_USER/zorvan.git
git push -u origin main
```

## 4) Set repo settings on GitHub

- Enable branch protection on `main`
- Require pull request + passing checks
- Enable Security Advisories
- Enable Discussions (optional but recommended)

## 5) Create first release tag

```powershell
git tag -a v0.1.0 -m "Zorvan v0.1.0"
git push origin v0.1.0
```

Then create a GitHub Release from tag `v0.1.0` with summary and known limitations.
