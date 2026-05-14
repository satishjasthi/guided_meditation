FROM python:3.12-slim

LABEL org.opencontainers.image.title="Guided Meditation"
LABEL org.opencontainers.image.description="Generate guided meditation audio using Kokoro-82M TTS. Fully offline, no network needed at runtime."
LABEL org.opencontainers.image.source="https://github.com/satishjasthi/guided_meditation"
LABEL org.opencontainers.image.authors="satishjasthi"
LABEL org.opencontainers.image.licenses="Apache-2.0"
LABEL org.opencontainers.image.version="0.2.0"

RUN apt-get update && \
    apt-get install -y --no-install-recommends espeak-ng libsndfile1 && \
    rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN UV_HTTP_TIMEOUT=300 uv sync --frozen --no-dev

COPY main.py meditation_script.json ./
COPY models/ models/

ENTRYPOINT ["uv", "run", "python", "main.py"]
CMD ["--minutes", "10", "--voice", "female"]
