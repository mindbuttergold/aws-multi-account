.PHONY: clean env format lint test help lock-deps install upgrade-deps

.DEFAULT_GOAL := help

env:
	hatch shell env

install:
	hatch run env:install-script-deps

format:
	ruff format

lint:
	hatch run env:lint-scripts

test:
	hatch run env:test-scripts

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
	@echo "setup-scripts makefile commands"
	@echo ""
	@echo "Usage:"
	@echo "  make <command>"
	@echo ""
	@echo "Commands:"
	@echo "  env           Start a Hatch shell in the default environment"
	@echo "  install       Install dependencies using Hatch script"
	@echo "  format        Format code with ruff"
	@echo "  lint          Run linters and type checking using Hatch script"
	@echo "  test          Run tests using Hatch script"
	@echo "  lock-deps     Create or update dependency lock files"
	@echo "  upgrade-deps  Update dependencies to latest versions and regenerate lock file"
	@echo "  clean         Clean cache directories"
