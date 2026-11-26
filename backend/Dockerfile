# The FastAPI service. Ollama itself is NOT in this image: it runs on the host,
# because the whole point is that the model uses the machine you already own.

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# PyMuPDF and Pillow need a few system libraries to read PDFs and images.
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p data/uploads data/chroma

EXPOSE 8000

# 127.0.0.1 on the host means the container must reach Ollama through
# host.docker.internal, which docker-compose.yml sets for you.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]