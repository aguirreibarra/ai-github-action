FROM python:3.12-slim

WORKDIR /app

# Install necessary dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends git ca-certificates curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Poetry with recommended method
ENV POETRY_VERSION=1.7.1
ENV POETRY_HOME=/opt/poetry
ENV POETRY_VENV=/opt/poetry-venv
ENV POETRY_CACHE_DIR=/opt/.cache

# Install poetry separated from system python
RUN python3 -m venv $POETRY_VENV \
    && $POETRY_VENV/bin/pip install -U pip setuptools \
    && $POETRY_VENV/bin/pip install poetry==$POETRY_VERSION

# Add poetry to PATH
ENV PATH="${PATH}:${POETRY_VENV}/bin"

# Configure poetry
RUN poetry config virtualenvs.create false

# Copy Poetry configuration files
COPY pyproject.toml poetry.lock* ./

# Install runtime dependencies
RUN poetry install --without dev --no-interaction --no-ansi

# Copy the action code
COPY . .

# Set the entrypoint
ENTRYPOINT ["python", "/app/main.py"]