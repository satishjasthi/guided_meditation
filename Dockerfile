FROM python:3.12-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends espeak-ng libsndfile1 && \
    rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY main.py meditation_script.json ./
COPY models/ models/

ENTRYPOINT ["uv", "run", "python", "main.py"]
CMD ["--minutes", "10", "--voice", "female"]
