.PHONY: help install install-dev test test-cov lint format typecheck clean build publish docs

help:
	@echo "Available commands:"
	@echo "  make install       Install the package in production mode"
	@echo "  make install-dev   Install the package in editable mode with dev dependencies"
	@echo "  make test          Run the test suite"
	@echo "  make test-cov      Run tests with coverage report"
	@echo "  make lint          Run linting checks (flake8)"
	@echo "  make format        Format code with black and isort"
	@echo "  make typecheck     Run type checking with mypy"
	@echo "  make clean         Remove build artifacts and cache files"
	@echo "  make build         Build distribution packages"
	@echo "  make publish       Upload package to PyPI (requires credentials)"
	@echo "  make docs          Generate documentation (if available)"

install:
	pip install -e .

install-dev:
	pip install --upgrade pip setuptools wheel
	pip install -e .[dev]
	@echo "✅ Development environment ready!"
	@echo "Consider running: pre-commit install"

test:
	pytest tests/ -v

test-cov:
	pytest tests/ -v --cov=chatfield --cov-report=term-missing --cov-report=html
	@echo "Coverage report generated in htmlcov/index.html"

lint:
	flake8 chatfield/ tests/
	@echo "✅ Linting passed!"

format:
	black chatfield/ tests/
	isort chatfield/ tests/
	@echo "✅ Code formatted!"

typecheck:
	mypy chatfield/
	@echo "✅ Type checking passed!"

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf chatfield.egg-info/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*~" -delete
	@echo "✅ Cleaned build artifacts and cache files!"

build: clean
	python -m build
	@echo "✅ Built distribution packages in dist/"

publish: build
	@echo "Publishing to PyPI..."
	twine check dist/*
	twine upload dist/*
	@echo "✅ Package published to PyPI!"

docs:
	@echo "Documentation generation not yet configured"
	@echo "Consider using Sphinx or MkDocs for documentation"

# Development workflow shortcuts
.PHONY: dev check ci

dev: format lint typecheck test
	@echo "✅ All development checks passed!"

check: lint typecheck test
	@echo "✅ All checks passed!"

ci: check
	@echo "✅ CI checks passed!"