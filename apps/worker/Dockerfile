FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/srv/moreai:/srv/moreai/apps/worker

WORKDIR /srv/moreai
RUN useradd --create-home --uid 10001 moreai
COPY apps/worker /srv/moreai/apps/worker
COPY engine /srv/moreai/engine
COPY apps/sandbox /srv/moreai/apps/sandbox
RUN pip install --no-cache-dir --disable-pip-version-check -r apps/worker/requirements.txt
USER 10001:10001
EXPOSE 8081
WORKDIR /srv/moreai/apps/worker
CMD ["python", "-m", "app.main"]
