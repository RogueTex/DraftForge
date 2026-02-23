.PHONY: install run check

install:
	pip install -r requirements.txt

run:
	uvicorn apps.api.main:app --reload --port 8010

check:
	python -m py_compile apps/api/main.py
