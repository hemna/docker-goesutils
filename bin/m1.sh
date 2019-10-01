#!/bin/bash
# This script is called with $path $file

source lib.sh

echo "Process new GOES m1 file $1 $2"
sleep 1

M1_DIR="$PROCESS_DIR/m1/$TODAY"
ensure_dir $M1_DIR

cp $1$2 $M1_DIR/$TIME.png
$SCRIPT_DIR/make_gif.sh $M1_DIR
