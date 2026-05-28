FROM python:3.11-slim

WORKDIR /workspace/services/processing-agent

ARG INSTALL_SENTENCE_TRANSFORMERS=false

COPY services/processing-agent/requirements-docker.txt ./requirements-docker.txt
COPY services/processing-agent/requirements-ml.txt ./requirements-ml.txt
RUN pip install --no-cache-dir -r requirements-docker.txt \
    && if [ "$INSTALL_SENTENCE_TRANSFORMERS" = "true" ]; then pip install --no-cache-dir -r requirements-ml.txt; fi

COPY services/processing-agent/app ./app
COPY schemas /workspace/schemas

ENV PYTHONPATH=/workspace/services/processing-agent

CMD ["python", "-m", "app.main"]
