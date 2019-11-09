#!/bin/bash

docker run -d \
    --name goesutils \
    --hostname goesutils \
    --user $(id -u):$(id -g) \
    -v /opt/docker/goestools/data:/home/goes/data \
    hemna/goesutils
