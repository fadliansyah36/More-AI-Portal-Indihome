FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/srv/moreai:/srv/moreai/apps/worker

WORKDIR /srv/moreai
RUN apt-get update && apt-get install -y --no-install-recommends tesseract-ocr tesseract-ocr-eng tesseract-ocr-ind && rm -rf /var/lib/apt/lists/*
RUN useradd --create-home --uid 10001 moreai
COPY apps/worker /srv/moreai/apps/worker
COPY engine /srv/moreai/engine
COPY apps/sandbox /srv/moreai/apps/sandbox
RUN pip install --no-cache-dir --disable-pip-version-check -r apps/worker/requirements.txt
USER 10001:10001
EXPOSE 8081
HEALTHCHECK --interval=30s --timeout=3s --start-period=90s --retries=3 CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8081/ready', timeout=2).read()"]
WORKDIR /srv/moreai/apps/worker
CMD ["python", "-m", "app.main"]
