.PHONY: test test-api test-ui install-test

PY ?= python3

install-test:
	$(PY) -m pip install -r requirements-dev.txt
	cd tests/ui && npm install
	$(PY) -m playwright install chromium

# tes API/unit (pytest)
test-api:
	$(PY) -m pytest tests -q

# tes UI (Playwright, headless)
test-ui:
	cd tests/ui && node run.js

test: test-api test-ui
