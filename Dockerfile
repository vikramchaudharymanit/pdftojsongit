# ── Stage 1: build dependencies ──────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build tools (needed to compile PyMuPDF wheels if a pre-built wheel
# is not available for this platform).
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        g++ \
        make \
        libmupdf-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# ── Stage 2: lean runtime image ───────────────────────────────────────────────
FROM python:3.11-slim AS runtime

WORKDIR /app

# Copy installed packages from the builder stage.
COPY --from=builder /install /usr/local

# Copy application source.
COPY main.py \
     pdf_reader.py \
     span_extractor.py \
     title_detector.py \
     heading_detector.py \
     json_writer.py \
     ./

# Default data directory (mount your PDFs here at runtime).
VOLUME ["/data"]

ENTRYPOINT ["python", "main.py"]
# Default to help-style invocation; override with actual paths at runtime.
CMD ["--help"]
