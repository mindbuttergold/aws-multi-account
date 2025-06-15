.PHONY: clean env format lint test help lock-deps install upgrade-deps

.DEFAULT_GOAL := help

env:
	hatch shell env

install:
	hatch run env:install-infra-deps

format:
	ruff format test_infrastructure.py

lint:
	hatch run env:lint-infra

test:
	hatch run env:test-infra

lock-deps:
	uv pip compile pyproject.toml -o requirements.lock

upgrade-deps:
	uv pip compile --upgrade pyproject.toml -o requirements.lock

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".coverage" -delete
	find . -type f -name ".coverage" -delete
	find . -type f -name "coverage.xml" -delete
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	@echo "IMPORTANT: If you're in a Hatch shell, type 'exit' to leave"

help:
	@echo "Available commands:"
	@echo "  env          Create and activate Hatch environment"
	@echo "  install      Install dependencies using Hatch script"
	@echo "  format       Format test_infrastructure.py"
	@echo "  lint         Run linting checks on test_infrastructure.py"
	@echo "  test         Run tests for test_infrastructure.py"
	@echo "  lock-deps    Generate requirements.lock from pyproject.toml"
	@echo "  upgrade-deps Update and regenerate requirements.lock files with latest dependency versions"
	@echo "  clean        Remove Python cache files"
