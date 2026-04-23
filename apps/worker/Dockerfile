FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /workspace

COPY apps/api/requirements.txt /workspace/apps/api/requirements.txt
RUN pip install --no-cache-dir -r /workspace/apps/api/requirements.txt

COPY apps/api /workspace/apps/api
COPY apps/worker /workspace/apps/worker
COPY packages/domain /workspace/packages/domain

WORKDIR /workspace

CMD ["python", "apps/worker/run_service.py"]
