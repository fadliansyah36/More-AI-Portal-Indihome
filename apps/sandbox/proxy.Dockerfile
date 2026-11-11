FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY apps/sandbox/app /app/apps/sandbox/app
CMD ["python", "-m", "apps.sandbox.app.browser_proxy_server"]
