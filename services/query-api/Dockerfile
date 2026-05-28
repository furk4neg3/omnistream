FROM python:3.11-slim

WORKDIR /workspace/services/query-api

ARG INSTALL_SENTENCE_TRANSFORMERS=false

COPY services/query-api/requirements-docker.txt ./requirements-docker.txt
COPY services/query-api/requirements-ml.txt ./requirements-ml.txt
RUN pip install --no-cache-dir -r requirements-docker.txt \
    && if [ "$INSTALL_SENTENCE_TRANSFORMERS" = "true" ]; then pip install --no-cache-dir -r requirements-ml.txt; fi

COPY services/query-api/app ./app
COPY schemas /workspace/schemas

ENV PYTHONPATH=/workspace/services/query-api

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
