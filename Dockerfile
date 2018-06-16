FROM python:3.6

ENV FLASK_APP enms.py

COPY enms.py gunicorn.py requirements.txt ./
COPY eNMS eNMS
COPY migrations migrations

RUN pip install -r requirements.txt

EXPOSE 5000
CMD ["gunicorn", "--config", "gunicorn.py", "enms:app"]