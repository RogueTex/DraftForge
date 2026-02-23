.PHONY: install install-dev run check test

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements-dev.txt

run:
	uvicorn apps.api.main:app --reload --port 8010

check:
	python3 -m py_compile apps/api/main.py apps/api/parsing.py

test:
	pytest -q
