#!/usr/bin/env just --justfile

# List all recipes
default:
    @just --list

# Build the project
build: install
    uv build

# Clean Python artifacts
clean:
    rm -rf build/
    rm -rf dist/
    rm -rf *.egg-info
    find . -type d -name __pycache__ -exec rm -rf {} +
    find . -type f -name "*.pyc" -delete

# Install dependencies
install:
    uv sync

# Run pre-commit checks
lint:
    ruff check tasks/

# Run tests
test *args:
    uv run -m pytest {{args}}

# Run the CLI application
run *args:
    uv run tasks/main.py {{args}}
