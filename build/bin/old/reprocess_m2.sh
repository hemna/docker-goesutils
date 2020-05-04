#!/bin/bash

# This script aims to nuke all the processed files
# for the FC images and then re process them

source lib.sh

echo "Let's reprocess '$M2'"
echo "nuke '$M2_DIR'"

rm -rf $M2_DIR

for entry in "$M2"/*.jpg
do
    dirpath=$(dirname $entry)
    filename=$(basename $entry)
    echo "Process '$dirpath' and file '$filename'"
    ANIMATION=false ./m2.sh $dirpath/ $filename
done

# Now that we are done, lets animate all of them
$SCRIPT_DIR/make_gif.sh $M2
