FROM python:3.11-slim

WORKDIR /code

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV DJANGO_SETTINGS_MODULE=SGUevents.settings
ENV PYTHONPATH=/code
RUN python manage.py collectstatic --noinput

EXPOSE 8887

CMD ["sh", "-c", "python manage.py makemigrations && python manage.py migrate && gunicorn SGUevents.wsgi:application --bind 0.0.0.0:8887"]
