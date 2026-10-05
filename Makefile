.PHONY: all up down demo eval test lint clean

PYTHON ?= python

all: up

up:
	docker compose up -d

down:
	docker compose down

demo:
	$(PYTHON) scripts/demo.py

eval:
	$(PYTHON) eval/run_all.py

test:
	pytest tests/ -v

lint:
	$(PYTHON) -m flake8 --max-line-length=120 ingest/ processor/ api/ cv/ rag/ eval/ scripts/ tests/ || true

train:
	$(PYTHON) scripts/train_anomaly.py

inject:
	$(PYTHON) scripts/inject.py

clean:
	rm -rf __pycache__ .pytest_cache eval/results/*.png eval/results/*.csv
