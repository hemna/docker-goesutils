#!/bin/bash
# This script is called with $path $file

source lib.sh
echo "Process new GOES Channel 15 file $1 $2"

CH15_DIR="$PROCESS_DIR/fd/$TODAY/ch15"
CH15_VA="$CH15_DIR/va"
CH15_CA="$CH15_DIR/ca"
sleep 1
crop_fd ch15 $1 $2
$SCRIPT_DIR/make_gif.sh $CH15_VA
$SCRIPT_DIR/make_gif.sh $CH15_CA
