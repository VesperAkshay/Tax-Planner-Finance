# ==============================================================================
# Production Dockerfile for Personal Finance + Tax Regime Planner Backend
# Compatible with Hugging Face Spaces (16GB Free Tier), Render, Fly.io, Railway
# ==============================================================================

FROM python:3.12-slim AS builder

WORKDIR /app

# Install system build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv package manager
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy project definition files
COPY pyproject.toml uv.lock ./

# Install production dependencies into /opt/venv
ENV UV_PROJECT_ENVIRONMENT="/opt/venv"
RUN uv sync --frozen --no-dev --no-install-project

# ==============================================================================
# Runtime Stage
# ==============================================================================
FROM python:3.12-slim AS runner

WORKDIR /app

# Install runtime libraries required by Docling, RapidOCR, OpenCV, and PDF parsers
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -m -u 1000 user

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH="/app/backend:/app"
ENV PYTHONUNBUFFERED=1
ENV MALLOC_ARENA_MAX=2
ENV PYTHONMALLOC=malloc
ENV OMP_NUM_THREADS=1
ENV MKL_NUM_THREADS=1
ENV NUMEXPR_NUM_THREADS=1
ENV VECLIB_MAXIMUM_THREADS=1

# Copy application code and required data assets
COPY backend/ /app/backend/
COPY data/tax_rules/ /app/data/tax_rules/
COPY data/rag/ /app/data/rag/
COPY data/categorization/ /app/data/categorization/

# Create runtime directories for ChromaDB and file uploads with proper ownership
RUN mkdir -p /app/data/chroma_db /app/data/chromadb /app/data/uploads /app/.cache && \
    chmod +x /app/backend/entrypoint.sh && \
    chown -R user:user /app

USER user

# Hugging Face Spaces exposes port 7860 by default
EXPOSE 7860

# Health check probe
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:${PORT:-7860}/health || exit 1

ENTRYPOINT ["/app/backend/entrypoint.sh"]
