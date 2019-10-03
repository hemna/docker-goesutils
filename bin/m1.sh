#!/bin/bash
# This script is called with $path $file

source lib.sh

echo "M1 file $1 $2"
sleep 1

ensure_dir $M1_DIR

# Get the time of the original file
FILE_TIME=$(TZ=GMT date -r $1$2 "+%H-%M-%S")
NEW_FILE="$M1_DIR/$FILE_TIME.png"

cp $1$2 $NEW_FILE
./date_overlay.sh $TZ_GMT $1$2 $NEW_FILE 12
$SCRIPT_DIR/make_gif.sh $M1_DIR
