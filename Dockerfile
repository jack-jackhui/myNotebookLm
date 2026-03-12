# Multi-stage build for smaller image size
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

# Final stage
FROM python:3.12-slim

LABEL authors="jackhui"
LABEL description="MyNotebookLM - Open Source AI Podcast Generator"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    STREAMLIT_SERVER_HEADLESS=true

WORKDIR /mynotebooklm

# Install runtime dependencies only (ffmpeg and curl for healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages from wheels
COPY --from=builder /wheels /wheels
RUN pip install --no-cache /wheels/* && rm -rf /wheels

# Copy application code
COPY . /mynotebooklm/

# Create data directories and set permissions
RUN mkdir -p /mynotebooklm/data/audio /mynotebooklm/data/transcripts /mynotebooklm/data/history \
    && chown -R nobody:nogroup /mynotebooklm

# Run as non-root user for security
USER nobody

# Expose the port
EXPOSE 8501

# Health check using Streamlit native endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Run streamlit
CMD ["streamlit", "run", "webui.py", "--server.port=8501", "--server.address=0.0.0.0"]
