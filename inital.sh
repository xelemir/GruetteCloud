#!/bin/bash

docker swarm init
docker network create --driver overlay --attachable gruetteChat-net
docker build -t chatapp ./flask
cd ./haproxy
docker build -t my_haproxy .
cd ..
docker stack deploy -c docker-compose.yml gruetteChat