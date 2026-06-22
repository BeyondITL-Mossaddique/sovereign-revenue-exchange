# syntax=docker/dockerfile:1.7
# Multi-stage build for the exchange-gateway service.

ARG PYTHON_VERSION=3.12

FROM python:${PYTHON_VERSION}-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:${PATH}"
COPY requirements.txt .
RUN pip install -r requirements.txt


FROM base AS test
COPY requirements-dev.txt .
RUN pip install -r requirements-dev.txt
COPY app ./app
COPY tests ./tests
ENV PYTHONPATH=/app
CMD ["pytest", "-q"]


FROM base AS openapi
COPY app ./app
RUN python -m app.main openapi /out/openapi.json


FROM python:${PYTHON_VERSION}-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:${PATH}"
WORKDIR /app
RUN groupadd --system --gid 1001 app && \
    useradd --system --uid 1001 --gid app --home-dir /app --shell /usr/sbin/nologin app
COPY --from=base /opt/venv /opt/venv
COPY --from=openapi /out/openapi.json /openapi/openapi.json
COPY --chown=app:app app ./app
USER app
EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=3s --retries=5 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/healthz').status==200 else 1)"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
