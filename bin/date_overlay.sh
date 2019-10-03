#!/bin/bash

# Script to add Date and Timestamp
# $1 = TZ
# $2 = Original file path
# $3 = image file to overlay
source lib.sh

HUMANDATE=$(TZ=$1 date -r $2 "+%A\ %b\ %e,\ %Y\ \ %T\ %Z")
FONT="$SCRIPT_DIR/Verdana_Bold.ttf"

#now add the stamp and such
echo "Add annotations $3"
convert $3 -quality 90 \
   -font $FONT \
   -fill '#0004' -draw 'rectangle 0,2000,2560,1820' \
   -pointsize 24 -gravity southwest \
   -fill white -gravity southwest -annotate +2+10 "$HUMANDATE" \
   -fill white -gravity southeast -annotate +2+10 "wx.hemna.com" \
    $3
