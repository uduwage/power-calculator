ARG PYTHON_VERSION=3.12-slim
FROM python:${PYTHON_VERSION}

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY pyproject.toml README.md LICENSE ./
COPY power_calculator ./power_calculator

RUN pip install --upgrade pip && pip install .

# Drop root privileges for runtime execution.
RUN groupadd --system app && useradd --system --create-home --gid app app \
    && chown -R app:app /app

USER app

ENTRYPOINT ["power-calculator"]
CMD ["--help"]
