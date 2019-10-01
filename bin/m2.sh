#!/bin/bash
# This script is called with $path $file

source lib.sh

echo "Process new GOES m2 file $1 $2"
sleep 1

M2_DIR="$PROCESS_DIR/m2/$TODAY"
ensure_dir $M2_DIR

cp $1$2 $M2_DIR/$TIME.png
$SCRIPT_DIR/make_gif.sh $M2_DIR
