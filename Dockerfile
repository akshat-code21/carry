# --- Build stage ---
FROM python:3.12-slim AS builder

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy dependency files first (for layer caching)
COPY pyproject.toml uv.lock* ./

# Install dependencies into the project venv
RUN uv sync --no-dev --no-install-project

# Copy source code
COPY . .

# Install the project itself
RUN uv sync --no-dev


# --- Runtime stage ---
FROM python:3.12-slim

# ffmpeg is required by yt-dlp for audio extraction (Whisper fallback)
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy the entire project with venv from builder
COPY --from=builder /app /app

# Add venv to PATH
ENV PATH="/app/.venv/bin:$PATH"

# Don't buffer Python output (important for Docker logs)
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

# Default: run the API server
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
