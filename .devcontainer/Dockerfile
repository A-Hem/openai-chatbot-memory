FROM mcr.microsoft.com/devcontainers/python:3.10-bullseye

# Install system packages
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends \
    build-essential \
    cmake \
    pkg-config \
    libffi-dev \
    libssl-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install Python dependencies
COPY requirements.txt /tmp/pip-tmp/
RUN pip3 --disable-pip-version-check --no-cache-dir install -r /tmp/pip-tmp/requirements.txt \
    && rm -rf /tmp/pip-tmp

# Install development tools
RUN pip3 --disable-pip-version-check --no-cache-dir install \
    black \
    mypy \
    pytest \
    pytest-cov \
    isort \
    flake8

# Create a non-root user
USER vscode

# Set working directory
WORKDIR /workspace