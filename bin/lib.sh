#!/bin/bash

TODAY=$(date '+%F')
#echo "Today = $TODAY"
TIME=$(date '+%H-%M-%S')
#echo "Time = $TIME"

SCRIPT_DIR="$(dirname $(readlink -f $0))"
#echo "SCRIPT_DIR='$SCRIPT_DIR'"

BASE_DIR="/home/goes/data"
PROCESS_DIR="$BASE_DIR/processed"

function ensure_dir {
  if [ ! -d "$1" ]; then
      mkdir -p $1
  fi
}

function crop_fd {
  # $1 contains the dest (false-color, ch15)
  # $2 contains the source dir
  # $3 contains the source image file name
  VA_CROP="$PROCESS_DIR/fd/$TODAY/$1/va"
  CA_CROP="$PROCESS_DIR/fd/$TODAY/$1/ca"

  ensure_dir $VA_CROP
  ensure_dir $CA_CROP

  # Lets create the VA crop
  NEW_FILE="$VA_CROP/$TIME.png"
  convert $2$3 -crop 1024x768+2100+600 +repage $NEW_FILE
  echo "$NEW_FILE done"

  # Create the CA Cropped image
  NEW_FILE="$CA_CROP/$TIME.png"
  convert $2$3 -crop 1024x768+600+600 $NEW_FILE
  echo "$NEW_FILE done"
}
