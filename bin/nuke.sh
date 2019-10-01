#!/bin/bash

for pid in $(pgrep monitor)
do
    kill $pid
done
