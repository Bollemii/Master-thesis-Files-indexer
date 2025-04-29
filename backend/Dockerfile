FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy


RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    libreoffice \
    default-jre \
    libreoffice-java-common \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

ADD ./app /app
COPY pyproject.toml .
COPY uv.lock .

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

ENV PATH="/app/.venv/bin:$PATH"

RUN mkdir -p /app/tmp

ENTRYPOINT []

CMD ["fastapi", "run", "main.py", "--port", "8000"]