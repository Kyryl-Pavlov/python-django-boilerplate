FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN addgroup --system app && adduser --system --ingroup app app
USER app

EXPOSE 5000

ENV DJANGO_SETTINGS_MODULE=app.settings.production

CMD ["gunicorn", "wsgi:application", "--bind", "0.0.0.0:5000", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker"]
