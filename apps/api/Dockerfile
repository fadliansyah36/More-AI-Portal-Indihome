FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/srv/api

WORKDIR /srv/api
RUN useradd --create-home --uid 10001 moreai
COPY apps/api /srv/api
RUN pip install --no-cache-dir --disable-pip-version-check -r requirements.txt
USER 10001:10001
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
