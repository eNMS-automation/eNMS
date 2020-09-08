# A baseline image for testing of the product
# Intended to run from the context of the projects ROOT (/) Directory
FROM python:3.6-slim-buster



RUN apt-get update -y
RUN apt-get install python3 -y
RUN apt-get install python3-pip -y
RUN apt-get install git -y
RUN apt-get install gcc -y
RUN apt-get install default-libmysqlclient-dev -y
RUN apt-get install libpq-dev python-dev -y
WORKDIR /opt/eNMS

# ------
# Copy source code
COPY eNMS eNMS
COPY setup setup
COPY files files
COPY docs docs
COPY logs logs
COPY scheduler scheduler
COPY app.py .
COPY gunicorn.py .
COPY package.json .
COPY setup.cfg .
COPY gunicorn.py .
COPY build/requirements/requirements.txt requirements.txt
COPY build/requirements/requirements.txt requirements.txt
COPY build/requirements/requirements_db.txt requirements_db.txt
COPY build/requirements/requirements_dev.txt requirements_dev.txt

COPY build/scripts/docker-boot.sh docker-boot.sh
RUN chmod +x docker-boot.sh
# ------
# App Dependencies Installation
#  - id_rsa key here so that the image within docker can do a signed pull from github
ADD build/docker/resources/id_rsa /root/.ssh/id_rsa

RUN mkdir -m 700 /root/.ssh; \
  touch -m 600 /root/.ssh/known_hosts; \
  ssh-keyscan github.com > /root/.ssh/known_hosts

#RUN ssh-keyscan -t rsa github.com > /root/.ssh/known_hosts
RUN pip3 install -r requirements.txt
RUN pip3 install -r requirements_db.txt


EXPOSE 5000
ENTRYPOINT ["./docker-boot.sh"]