# Use a Python image with uv pre-installed
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

# Enable bytecode compilation and set link mode for uv
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# Install dependencies using uv and the lockfile
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

# Copy the rest of the project source code
ADD . /app

# Install the project itself (editable mode, no dev deps)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# Add the app directory to PYTHONPATH for imports
ENV PYTHONPATH="/app:${PYTHONPATH}"

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"

# Set the entrypoint to run your main script
ENTRYPOINT ["python", "/app/src/main.py"]