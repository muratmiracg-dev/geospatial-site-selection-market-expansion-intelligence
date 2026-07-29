.PHONY: install pipeline api lint format test audit verify all

install:
	python -m pip install -e ".[dev]"

pipeline:
	site-intelligence run --config configs/base.yaml

api:
	uvicorn site_intelligence.api.app:app --host 0.0.0.0 --port 8000

lint:
	ruff format --check .
	ruff check .

format:
	ruff format .
	ruff check --fix .

test:
	pytest --cov=site_intelligence --cov-report=term-missing --cov-report=xml --cov-fail-under=90

audit:
	pip-audit

verify:
	python scripts/verify_artifacts.py

all: lint test verify

