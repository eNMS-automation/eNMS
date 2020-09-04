# eNMS Docker Deployment

## Summary


These images are intended to allow an everyday person to quickly jumpstart the eNMS usage. For "pickup and go" usage.

There are multiple strategies for deployment included in this directory.

These deployment strategies are a good double for setting up a testing environment quickly on a local network as well.
- [eNMS Docker Deployment](#enms-docker-deployment)
  - [Summary](#summary)
  - [Get up and running in minutes](#get-up-and-running-in-minutes)
    - [Non Production](#non-production)
    - [Optional commands](#optional-commands)
    - [Building the docker image from source](#building-the-docker-image-from-source)

## Get up and running in minutes

Get up and running with eNMS in minutes.

### Non Production
 1. install docker 
```wget -O getdocker.sh https://get.docker.com/```

 2. give docker install script permission to run `chmod +x getdocker.sh`
 3. run the container `docker run --name eNMS -p 80:5000 gnubyte/enms:latest` and wait a minute or so
 
 ### Optional commands 

Run without your console attached to the logs

 ```docker run -d --name enms -p 80:5000 gnubyte/enms:latest```


 -  stop the container running the software: `docker stop enms`
 - check running software status: `docker ps`




### Building the docker image from source

With docker installed: 

` docker build  -f build/docker/Dockerfile -t enms:latest . `

