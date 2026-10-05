FROM python:3.11-slim
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir aiokafka requests
CMD ["python", "ingest/fetch_flights.py"]
