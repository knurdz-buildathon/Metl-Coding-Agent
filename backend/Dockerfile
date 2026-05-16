FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for Playwright, Aider, etc.
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    build-essential \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Playwright browsers for browser-use
RUN pip install playwright && \
    playwright install chromium && \
    playwright install-deps chromium

# Copy source first for pip install
COPY . .

# Install core dependencies + test tools
RUN pip install --no-cache-dir -e .

# Install test and dev tools directly
RUN pip install --no-cache-dir \
    pytest>=8.0.0 \
    pytest-asyncio>=0.25.0 \
    pytest-cov>=6.0.0 \
    httpx>=0.28.0 \
    ruff>=0.9.0 \
    mypy>=1.15.0

# Optional: install v0-sdk if flag is set
ARG INSTALL_V0=false
RUN if [ "$INSTALL_V0" = "true" ]; then pip install v0-sdk; fi

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]