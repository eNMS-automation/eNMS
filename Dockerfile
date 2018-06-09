FROM python:3.6

ENV FLASK_APP enms.py

COPY gentelella.py gunicorn_config.py requirements.txt ./
COPY eNMS eNMS
COPY migrations migrations

RUN pip install -r requirements.txt

EXPOSE 5000
CMD ["gunicorn", "--config", "gunicorn.py", "gentelella:eNMS"]