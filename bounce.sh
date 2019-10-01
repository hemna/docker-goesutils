#!/bin/bash

NAME="goesutils"
ID=$(docker ps -a -f name=$NAME -q)
docker container stop $ID
docker container rm $ID

./run-it.sh
