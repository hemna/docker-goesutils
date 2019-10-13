#!/bin/bash

source lib.sh

# Make a gif out of a directory of images
# Dir is $1
# gif is always named 'animation.gif'

FILE="$1/animation.gif"
convert -loop 0 -delay 15 $1/*.png $FILE
echo "Done creating $FILE"
