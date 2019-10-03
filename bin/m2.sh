#!/bin/bash
# This script is called with $path $file

source lib.sh

echo "M2 file $1 $2"
sleep 1

ensure_dir $M2_DIR

# Get the time of the original file
FILE_TIME=$(TZ=GMT date -r $1$2 "+%H-%M-%S")
NEW_FILE="$M2_DIR/$FILE_TIME.png"

cp $1$2 $NEW_FILE
./date_overlay.sh $TZ_GMT $1$2 $NEW_FILE 12
$SCRIPT_DIR/make_gif.sh $M2_DIR
