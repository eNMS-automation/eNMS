# eNMS Docker Deployment

[![DockerLogo](https://www.docker.com/sites/default/files/d8/2019-07/horizontal-logo-monochromatic-white.png)](https://www.docker.com/sites/default/files/d8/2019-07/horizontal-logo-monochromatic-white.png)


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
  - [Docker Compose](#docker-compose)
    - [Install Docker Compose](#install-docker-compose)
    - [Run the Compose File](#run-the-compose-file)
      - [Run the Compose File Daemonized](#run-the-compose-file-daemonized)
      - [Tail the Compose Services Logs](#tail-the-compose-services-logs)
    - [Edit the configuration](#edit-the-configuration)
    - [Inspect the configuration](#inspect-the-configuration)

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



------

## Docker Compose 

[![DockerLogo](https://lh4.googleusercontent.com/LSPoTqqdMnwNshGXT0-DfghvSqJD-iLOHw_sg1J1E2115J_0OROkoxw8ELLseBKZl952sCiNunbzCoNl4bj1u7RFhY5QtFK8ms_G9HIWZlw40zBZS4iVtKPw0Zgfc6vVJeZZGT1d)](https://lh4.googleusercontent.com/LSPoTqqdMnwNshGXT0-DfghvSqJD-iLOHw_sg1J1E2115J_0OROkoxw8ELLseBKZl952sCiNunbzCoNl4bj1u7RFhY5QtFK8ms_G9HIWZlw40zBZS4iVtKPw0Zgfc6vVJeZZGT1d)




The Docker compose tool is an extra binary that docker offers to help bring out and separate an entire blueprint for an environment. IE you can specify a container for a database separately from your application, then connect them through the blueprint.

### Install Docker Compose

[Docker compose install guide from Dockers own site](https://docs.docker.com/compose/install/)



### Run the Compose File

This process will fetch & begin running the software in each container. It additionally specifies the passwords to set from the `env.sh` file.

Running this will interactively follow the logs of each container.

```docker-compose -f build/docker/docker-compose.yml --env-file build/docker/resources/env.sh config```

#### Run the Compose File Daemonized

This will run the containers in the background instead of interactively in the foreground.

```docker-compose  -d -f build/docker/docker-compose.yml --env-file build/docker/resources/env.sh config```

#### Tail the Compose Services Logs

Follows the logs in these services interactively as if you ran `tail -f <file>`.

```docker-compose -f build/docker/docker-compose.yml logs -f```

### Edit the configuration

The configuration for the docker compose blueprint exists in two places
 1. `build/docker/docker-compose.yml`
 2. `build/docker/resources/env.sh`
 3. `build/docker/resources/mysql/init.sql`


**Blueprint via Docker Compose file**
The first file - compose file - is the declaration of each containerized service. It is where attributes of the services, and customizations of the services themselves are linked to the service described.


**Passwords env.sh**
The second file is used to dynamically plug in passwords into the compose file. It will be used to load environment variables into the runtime.

**MySQL configuration**
There is an SQL query file that is ran on initiation of the MySQL service. This gives the application level user access to the database. 


### Inspect the configuration

With Docker compose installed, inspect the relationship of the `env.sh` configuration file as it will populate the compose file

```
docker-compose -f build/docker/docker-compose.yml --env-file build/docker/resources/env.sh config
```