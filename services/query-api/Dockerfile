FROM python:3.11-slim

ARG APP_UID=1000
ARG APP_GID=1000
ARG INSTALL_SENTENCE_TRANSFORMERS=false

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/workspace/services/query-api

WORKDIR /workspace/services/query-api

RUN groupadd --gid "${APP_GID}" omnistream \
    && useradd --uid "${APP_UID}" --gid omnistream --create-home --home-dir /home/omnistream omnistream \
    && mkdir -p /workspace/local-data/events \
        /workspace/local-data/enriched \
        /workspace/local-data/state \
        /workspace/local-data/vector_store \
        /workspace/local-data/model-cache \
    && chown -R omnistream:omnistream /workspace /home/omnistream

COPY services/query-api/requirements-docker.txt ./requirements-docker.txt
COPY services/query-api/requirements-ml.txt ./requirements-ml.txt
RUN pip install --no-cache-dir -r requirements-docker.txt \
    && if [ "$INSTALL_SENTENCE_TRANSFORMERS" = "true" ]; then pip install --no-cache-dir -r requirements-ml.txt; fi

COPY --chown=omnistream:omnistream services/query-api/app ./app
COPY --chown=omnistream:omnistream schemas /workspace/schemas

USER omnistream

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
