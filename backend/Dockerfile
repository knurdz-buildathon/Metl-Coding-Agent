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

COPY pyproject.toml .
RUN pip install --no-cache-dir -e ".[dev]"

# Install optional deps based on env flags
ARG INSTALL_V0=false
RUN if [ "$INSTALL_V0" = "true" ]; then pip install v0-sdk; fi

ARG INSTALL_CURSOR=false
RUN if [ "$INSTALL_CURSOR" = "true" ]; then pip install cursor-sdk; fi

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]