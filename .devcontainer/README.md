# Dev Container Setup

This directory contains the configuration for developing in a Docker container using VS Code/Cursor's Remote-Containers feature.

## Usage

1. **Open in Container**: 
   - In VS Code/Cursor, press `F1` (or `Ctrl+Shift+P` / `Cmd+Shift+P`)
   - Select "Dev Containers: Reopen in Container"
   - The container will build and start automatically

2. **First Time Setup**:
   - The container will build (this may take a few minutes the first time)
   - After building, `postCreateCommand` will run `maturin develop` to build the Rust extension
   - You're ready to code!

## What's Included

- **Python 3.11** with virtual environment at `/opt/venv`
- **Rust** stable toolchain
- **All Python dependencies** from `pyproject.toml` (dev dependencies included)
- **VS Code/Cursor extensions** for Python, Rust, and Jupyter
- **Port forwarding** for Jupyter (8888) and application (8000)

## Rebuilding the Rust Extension

The Rust extension is automatically built when the container is created. To rebuild manually:

```bash
maturin develop
```

Or for a release build:

```bash
maturin develop --release
```

## Rust Build Caching

Rust build artifacts are stored in `rust/target/`. This directory is excluded from the workspace mount (via `.dockerignore`) to avoid permission issues. If you need to persist Rust build cache between container rebuilds, you can:

1. Use a Docker volume for the target directory
2. Or remove `target/` from `.dockerignore` (may cause permission issues)

## Troubleshooting

- **Container won't start**: Check that Docker is running
- **Rust extension not found**: Run `maturin develop` manually
- **Port conflicts**: Adjust port numbers in `devcontainer.json`
- **Slow rebuilds**: The Rust extension rebuilds on container start; this is normal
