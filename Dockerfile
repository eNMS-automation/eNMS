FROM python:3.6

ENV FLASK_APP app.py

COPY app.py boot.sh gunicorn.py requirements.txt .env .env-pgsql ./
COPY applications applications
COPY eNMS eNMS
COPY logs logs
COPY migrations migrations
COPY projects projects

RUN pip install -r requirements.txt

EXPOSE 5000

RUN chmod +x ./boot.sh

ENTRYPOINT ["./boot.sh"]
