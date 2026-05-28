FROM python:3.11-slim

WORKDIR /workspace/services/producer

COPY services/producer/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY services/producer/app ./app
COPY schemas /workspace/schemas

ENV PYTHONPATH=/workspace/services/producer

CMD ["python", "-m", "app.main"]
