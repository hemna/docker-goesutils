#!/bin/bash

# This script aims to nuke all the processed files
# for the FC images and then re process them

source lib.sh

# get the list of all of the files in $FALSECOLOR
echo "Let's reprocess '$M1'"
echo "nuke '$M1_DIR'"

# nuke all entries in $CH15_DIR
rm -rf $M1_DIR

for entry in "$M1"/*.jpg
do
    dirpath=$(dirname $entry)
    filename=$(basename $entry)
    echo "Process '$dirpath' and file '$filename'"
    ANIMATION=false ./m1.sh $dirpath/ $filename
done

# Now that we are done, lets animate all of them
$SCRIPT_DIR/make_gif.sh $M1
