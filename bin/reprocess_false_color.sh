#!/bin/bash

# This script aims to nuke all the processed files
# for the FC images and then re process them

source lib.sh

# get the list of all of the files in $FALSECOLOR
echo "Let's reprocess '$FALSECOLOR'"
echo "nuke '$FC_DIR'"

# nuke all entries in $FC_DIR
rm -rf $FC_DIR

for entry in "$FALSECOLOR"/*.png
do
    dirpath=$(dirname $entry)
    filename=$(basename $entry)
    echo "Process '$dirpath' and file '$filename'"
    ANIMATION=false ./false_color.sh $dirpath/ $filename
done

# Now that we are done, lets animate all of them
$SCRIPT_DIR/make_gif.sh $FC_VA
$SCRIPT_DIR/make_gif.sh $FC_CA
