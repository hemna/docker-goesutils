#!/bin/bash
# This script is called with $path $file
source lib.sh

ANIMATION=${ANIMATION:-true}
echo "Process new GOES false color file $1 $2"

# give the image time to be written to disk
sleep 1
crop_fd false-color $1 $2

if [ "$ANIMATION" == true ]; then
  $SCRIPT_DIR/make_gif.sh $FC_VA
  $SCRIPT_DIR/make_gif.sh $FC_CA
fi
