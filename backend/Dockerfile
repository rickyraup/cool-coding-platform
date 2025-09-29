# Dockerfile for Python code execution environment
# Base image with Python 3.11
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies and Node.js
RUN apt-get update && apt-get install -y \
    bash \
    curl \
    git \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd -r codeuser && useradd -r -g codeuser -u 1000 codeuser

# Set up Python environment with required packages
RUN pip install --no-cache-dir \
    pandas==2.1.3 \
    numpy==1.25.2 \
    scipy==1.11.4 \
    matplotlib==3.8.2 \
    requests==2.31.0 \
    jupyter==1.0.0 \
    ipython==8.17.2

# Create app directory and home directory with proper ownership
RUN mkdir -p /app /home/codeuser && chown -R codeuser:codeuser /app /home/codeuser

# Switch to non-root user
USER codeuser

# Set working directory
WORKDIR /app

# Set up Python path
ENV PYTHONPATH=/app

# Default command starts bash shell
CMD ["/bin/bash"]