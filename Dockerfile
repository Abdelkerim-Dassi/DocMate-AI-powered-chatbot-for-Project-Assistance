# Stage 1: Base image with required build dependencies
FROM python:3.10-slim as base-stage

# Install system dependencies for building Python packages and curl
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    cmake \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Stage 2: Install Poetry and export requirements
FROM base-stage as poetry-requirements-stage

WORKDIR /tmp

ENV HOME=/root
ENV PATH=$PATH:$HOME/.local/bin

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | POETRY_VERSION=1.5.1 python3 -

# Copy Poetry configuration files
COPY ./pyproject.toml ./poetry.lock* /tmp/

# Export dependencies to a requirements.txt file
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes

# Stage 3: Final image with runtime dependencies
FROM python:3.10-slim as runtime-stage

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libffi-dev \
    openssl \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

ENV \
    PYTHONUNBUFFERED=1 \
    PIP_DEFAULT_TIMEOUT=600 \
    PIP_NO_CACHE_DIR=1 \
    UVICORN_HOST="0.0.0.0" \
    UVICORN_PORT=8100

# Copy dependencies from poetry-requirements-stage
COPY --from=poetry-requirements-stage /tmp/requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

RUN chmod -R 777 /app


# Copy application source code
COPY . /app

# Add and set a non-root user for security
USER 1000

# Expose the application port
EXPOSE 8100

# Start FastAPI application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8100"]
