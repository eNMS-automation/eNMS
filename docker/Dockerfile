FROM python:3.6

ENV FLASK_APP app.py

COPY app.py boot.sh gunicorn.py requirements.txt package.json ./
COPY applications applications
COPY eNMS eNMS
COPY git git
COPY nginx nginx
COPY logs logs
COPY projects projects

RUN pip install -r requirements.txt

EXPOSE 5000

RUN chmod +x ./boot.sh

ENTRYPOINT ["./boot.sh"]
