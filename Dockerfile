FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY api/ api/
COPY build/markers_normalized/ build/markers_normalized/
COPY mcp_server.py .

RUN mkdir -p personas

ENV PORT=8420

EXPOSE ${PORT}

CMD uvicorn api.main:app --host 0.0.0.0 --port ${PORT}
