FROM python:3.6

ENV FLASK_APP app.py

COPY app.py config.py gunicorn.py requirements.txt ./
COPY eNMS eNMS
COPY migrations migrations
COPY projects projects

RUN pip install -r requirements.txt

EXPOSE 5000
CMD ["gunicorn", "--config", "gunicorn.py", "app:app"]