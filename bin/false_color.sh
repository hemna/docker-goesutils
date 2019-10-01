#!/bin/bash
# This script is called with $path $file
source lib.sh
echo "Process new GOES false color file $1 $2"

# give the image time to be written to disk
FC_DIR="$PROCESS_DIR/fd/$TODAY/false-color"
FC_VA="$FC_DIR/va"
FC_CA="$FC_DIR/ca"
sleep 1
crop_fd false-color $1 $2
$SCRIPT_DIR/make_gif.sh $FC_VA
$SCRIPT_DIR/make_gif.sh $FC_CA
