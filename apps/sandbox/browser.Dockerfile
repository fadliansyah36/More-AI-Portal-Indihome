FROM mcr.microsoft.com/playwright/python:v1.55.0-noble
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY apps/sandbox/requirements-browser.txt /app/requirements-browser.txt
RUN pip install --no-cache-dir -r /app/requirements-browser.txt
COPY apps/sandbox/app /app/apps/sandbox/app
CMD ["uvicorn", "apps.sandbox.app.browser_service:app", "--host", "0.0.0.0", "--port", "8080"]
