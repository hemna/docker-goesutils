#!/bin/bash

# Script to add Date and Timestamp
# $1 = TZ
# $2 = Original file path
# $3 = image file to overlay
# $4 font size
source lib.sh

HUMANDATE=$(TZ="$1" date -r $2 "+%A\ %b\ %e,\ %Y\ \ %T\ %Z")
FONT="$SCRIPT_DIR/Verdana_Bold.ttf"

if [ -z "$4" ]; then
    font=24
else
    font=$4
fi


#now add the stamp and such
echo "Add annotations $3"
convert $3 -quality 90 \
   -font $FONT \
   -fill '#0004' -draw 'rectangle 0,2000,2560,1820' \
   -pointsize $font -gravity southwest \
   -fill white -gravity southwest -annotate +2+10 "$HUMANDATE" \
   -fill white -gravity southeast -annotate +2+10 "wx.hemna.com" \
    $3
