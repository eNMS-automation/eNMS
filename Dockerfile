FROM python:3.6

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY gunicorn_config.py .

COPY source /app

EXPOSE 5100

CMD ["gunicorn", "--chdir", "app", "--config", "./gunicorn_config.py", "flask_app:app"]
