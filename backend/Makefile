.PHONY: dev setup test lint typecheck fmt

setup:
	python -m pip install -r requirements/dev.txt

dev: setup
	python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --app-dir .

test:
	pytest -q

lint:
	ruff check .

typecheck:
	mypy app
