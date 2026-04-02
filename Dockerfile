# ABOUTME: Production Dockerfile for ethica API service
# ABOUTME: Optimized for Google Cloud Run (small image, non-root user, git included)

FROM python:3.12-slim

# Git is required to clone repos for checking
RUN apt-get update && \
    apt-get install -y --no-install-recommends git && \
    rm -rf /var/lib/apt/lists/*

# Run as non-root
RUN useradd --create-home ethica
USER ethica
WORKDIR /home/ethica/app

# Install dependencies first (layer caching)
COPY --chown=ethica:ethica pyproject.toml setup.py ./
COPY --chown=ethica:ethica ethica/__init__.py ethica/__init__.py
RUN pip install --no-cache-dir --user ".[server]"

# Copy the rest of the application
COPY --chown=ethica:ethica . .
RUN pip install --no-cache-dir --user -e .

# Cloud Run sets $PORT; default to 8080
ENV PORT=8080
ENV PATH="/home/ethica/.local/bin:${PATH}"

EXPOSE ${PORT}

CMD uvicorn ethica.api.server:app --host 0.0.0.0 --port ${PORT}
