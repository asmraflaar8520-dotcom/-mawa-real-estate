FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Seed demo data (properties, agents, images) at build time
RUN python -m backend.app.utils.seed_data

# Hugging Face Spaces expects port 7860; other hosts can override PORT
ENV PORT=7860
EXPOSE 7860

CMD ["sh", "-c", "uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT}"]
