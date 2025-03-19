#!/usr/bin/env just --justfile

# List all recipes
default:
    @just --list

# Install project dependencies
install:
    pip install -e ".[dev]"
    pre-commit install

# Run pre-commit checks
lint:
    pre-commit run --all-files

# Run tests
test:
    pytest

# Clean Python artifacts
clean:
    rm -rf build/
    rm -rf dist/
    rm -rf *.egg-info
    find . -type d -name __pycache__ -exec rm -rf {} +
    find . -type f -name "*.pyc" -delete

# Build the project
build:
    pip install build
    python -m build

# Run the CLI application
run *args:
    python -m tasks.main {{args}}
