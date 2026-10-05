FROM python:3.11-slim
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir aiokafka asyncpg scikit-learn joblib numpy
CMD ["python", "processor/main.py"]
