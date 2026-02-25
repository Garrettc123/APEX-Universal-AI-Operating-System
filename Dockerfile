# ── Build stage ──────────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

# Install system dependencies needed only for compiling wheels
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies into the apex user's home
# FIX: install to /home/apex/.local so non-root user can execute them in runtime stage
RUN useradd -m -u 1000 apex
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ── Runtime stage ─────────────────────────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# Recreate the same non-root user with the same UID
RUN useradd -m -u 1000 apex && \
    chown -R apex:apex /app

# FIX: Copy packages from builder's /root/.local → apex's /home/apex/.local
# so the apex user can actually execute binaries installed there
COPY --from=builder --chown=apex:apex /root/.local /home/apex/.local

# Copy application code
COPY --chown=apex:apex app.py .
COPY --chown=apex:apex main.py .
COPY --chown=apex:apex src/ ./src/

# FIX: Set PATH to apex user's .local/bin (not root's)
ENV PATH=/home/apex/.local/bin:$PATH

# Switch to non-root user
USER apex

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Run the application via the canonical entrypoint
CMD ["python", "main.py"]
