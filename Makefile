.PHONY: install install-dev test test-unit test-contract lint fmt clean run-daemon run-status run-events audit-verify

VENV   := .venv
PY     := $(VENV)/bin/python
PIP    := $(VENV)/bin/pip
PYTEST := $(VENV)/bin/pytest
RUFF   := $(VENV)/bin/ruff
SGD    := $(VENV)/bin/sgd
SG     := $(VENV)/bin/sg

FIXTURE_CONFIG := tests/fixtures/configs/basic.toml

# ── Install ───────────────────────────────────────────────────────────────────

install:
	python3 -m venv $(VENV)
	$(PIP) install -e .

install-dev:
	python3 -m venv $(VENV)
	$(PIP) install -e ".[dev]"

# ── Test ──────────────────────────────────────────────────────────────────────

test: test-unit test-contract

test-unit:
	$(PYTEST) tests/unit/ -v

test-contract:
	$(PYTEST) tests/contract/ -v

# ── Lint & Format ─────────────────────────────────────────────────────────────

lint:
	$(RUFF) check serverguard/ tests/

fmt:
	$(RUFF) format serverguard/ tests/

fmt-check:
	$(RUFF) format --check serverguard/ tests/

# ── Run ───────────────────────────────────────────────────────────────────────

run-daemon:
	$(SGD) --config $(FIXTURE_CONFIG) --replay

run-status:
	$(SG) status --config $(FIXTURE_CONFIG)

run-events:
	$(SG) events --config $(FIXTURE_CONFIG)

audit-verify:
	$(SG) audit verify --config $(FIXTURE_CONFIG)

# ── Clean ─────────────────────────────────────────────────────────────────────

clean:
	rm -rf $(VENV) __pycache__ .pytest_cache dist *.egg-info .coverage htmlcov
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	rm -rf tmp/ data/
