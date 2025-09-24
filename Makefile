.PHONY: help build install test fmt doc dist clean

# Default target
help:
	@echo "Available targets:"
	@echo "  build   - Create the project environment and build project"
	@echo "  install - Install the project"
	@echo "  test    - Run test suite with pytest"
	@echo "  fmt     - Run linting checks with black, flake8 and isort"
	@echo "  doc     - Build and install man files"
	@echo "  dist    - Create pypi distribution package"
	@echo "  clean   - Clean build artifacts"

# Create the project environment and build project
build:
	@echo "Creating/using conda env 'confy' and installing dev dependencies"
	@if command -v conda >/dev/null 2>&1; then \
		if ! conda env list | awk '{print $$1}' | grep -qx confy; then \
			echo "Creating conda env 'confy'..."; \
			conda create -n confy python=3.11 -y; \
		else \
			echo "Conda env 'confy' already exists"; \
		fi; \
		echo "Installing editable package into 'confy'..."; \
		conda run -n confy python -m pip install -e .[dev]; \
	else \
		echo "conda not found, falling back to system pip"; \
		python -m pip install -e .[dev]; \
	fi

# Install the project
install:
	python -m pip install .

# Run test suite with pytest
test:
	python -m pytest test/ -v

# Run linting checks with black, flake8 and isort
fmt:
	python -m black --check src/ test/
	python -m isort --check-only src/ test/
	python -m flake8 src/ test/

# Fix formatting issues
fmt-fix:
	python -m black src/ test/
	python -m isort src/ test/

# Build and install man files
doc:
	@echo "Documentation target - man files would be built here"
	@mkdir -p doc/man
	@echo "Man page generation not yet implemented"

# Create pypi distribution package
dist:
	python -m pip install --upgrade build wheel twine packaging readme-renderer setuptools
	python -m build

# Clean build artifacts
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete