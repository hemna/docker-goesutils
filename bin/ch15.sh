#!/bin/bash
# This script is called with $path $file

source lib.sh
ANIMATION=${ANIMATION:-true}
echo "Process new GOES Channel 15 file $1 $2"

sleep 1
crop_fd ch15 $1 $2

if [ "$ANIMATION" == true ]; then
  $SCRIPT_DIR/make_gif.sh $CH15_VA
  $SCRIPT_DIR/make_gif.sh $CH15_CA
fi
