.PHONY: test test-quick test-frontend lint pii-scan install

# Medical Monitoring Workbench - M1 可复现基线
# 一条命令在干净克隆上跑全部测试

VENV := .venv
PY := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

install:
	$(PIP) install -r services/api/requirements.txt -r services/api/requirements-dev.txt

test: lint pii-scan test-quick test-frontend

test-quick:
	cd $(CURDIR) && $(PY) -m pytest tests/ -q -p no:cacheprovider --timeout=300 --skip-local-only -x

test-frontend:
	cd frontend && npm test

lint:
	$(VENV)/bin/ruff check --select F821 packages/ services/ --exit-zero

pii-scan:
	$(PY) scripts/ci/pii_scan.py
