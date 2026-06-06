FROM python:3.11-slim

ARG APP_UID=1000
ARG APP_GID=1000

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/workspace/services/producer

WORKDIR /workspace/services/producer

RUN groupadd --gid "${APP_GID}" omnistream \
    && useradd --uid "${APP_UID}" --gid omnistream --create-home --home-dir /home/omnistream omnistream \
    && mkdir -p /workspace/local-data/events \
        /workspace/local-data/enriched \
        /workspace/local-data/state \
        /workspace/local-data/vector_store \
        /workspace/local-data/model-cache \
    && chown -R omnistream:omnistream /workspace /home/omnistream

COPY services/producer/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=omnistream:omnistream services/producer/app ./app
COPY --chown=omnistream:omnistream schemas /workspace/schemas

USER omnistream

CMD ["python", "-m", "app.main"]
