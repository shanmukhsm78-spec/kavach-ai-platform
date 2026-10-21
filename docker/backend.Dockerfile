FROM python:3.12-slim
WORKDIR /app
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY backend /app/backend
COPY agents /app/agents
COPY modes /app/modes
COPY datasets /app/datasets
RUN mkdir -p /app/data/attack /app/data/defend /app/data/protect
ENV KAVACH_LLM=off
ENV PYTHONPATH=/app/backend:/app
WORKDIR /app/backend
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
