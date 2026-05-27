# Zorvan

Zorvan is a repository for implementing computational graph architectures and experiments across different modeling paradigms (MLP, ANFIS, Fuzzy Systems, Evolutionary Algorithms).

> Note: internal Python package/module paths have been renamed to `zorvan` starting with v0.1.0.

## 🚀 Quick Start

```powershell
# Run visual editor
python run_new_ui.py
```

```powershell
# Build a Windows standalone executable locally
.\scripts\build_exe.ps1
```

To use the Zorvan icon in the built application, place `zorvan.ico` into the `assets/` folder.
If the file exists, the build script will use it for both the executable icon and the app window icon.

### GitHub release automation
A Windows executable can also be produced by GitHub Actions when a tag matching `v*` is pushed.
The workflow is defined in `.github/workflows/build_windows_exe.yml`, and it uploads `dist\ZorvanNewUI.exe` as an artifact.

## � Example Usage Scripts
The `zorvan/Examples/` folder contains user-facing demo scripts, not automated tests. Run them from the repository root so that `zorvan` is on `PYTHONPATH`, for example:

```powershell
python zorvan/Examples/FibonacciExample.py
```

The examples now also adjust `sys.path` automatically so they work from other working directories.

## �📚 Documentation

- **[GUI README](docs/GUI_README.md)** - Visual editor features and usage
- **[GUI Rebuild Project](docs/gui_rebuild/)** - Modern MVVM architecture migration (in progress)
- **[Examples Features](docs/EXAMPLES_FEATURES.md)** - Pre-built example graphs
- **[Architecture Comparison](docs/ARCHITECTURE_COMPARISON.md)** - Concurrent vs Forward processing
- **[Copilot Guide](docs/COPILOT_README.md)** - Agent usage and conventions
- **[Contributing](CONTRIBUTING.md)** - Development guidelines
- **[Developer Guide](docs/DEVELOPER_GUIDE.md)** - TDD, pre-commit hooks, git-cz

## 🔧 Development

See `docs/AGENT_POLICY.md` for agent usage guidance and contribution rules. Use `CONTRIBUTING.md` for guidelines, and run `scripts/run_checks.ps1` to validate code locally.

For public launch steps, see `PUBLISH_ZORVAN.md` and `ZORVAN_RELEASE_PLAN.md`.
