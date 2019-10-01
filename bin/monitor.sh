#!/bin/bash
source lib.sh

GOESDATA="/home/goes/data"
FALSECOLOR="$GOESDATA/goes16/fd/$TODAY/false-color/"
CH15="$GOESDATA/goes16/fd/$TODAY/ch15_enhanced/"
M1="$GOESDATA/goes16/m1/$TODAY/ch13_enhanced"
M2="$GOESDATA/goes16/m2/$TODAY/ch13_enhanced"
EMWIN="$GOESDATA/emwin/$TODAY/"

function monitor() {
    echo "Setup monitor for $1 and run $2"
inotifywait -m $1 -e create |
  while read path action file; do
    #echo "The file '$file' appeared in dir '$path' via '$action'"
    #echo "call $2 $path $file"
    call=$($SCRIPT_DIR/$2 $path $file)
    echo $call
  done
}


monitor $FALSECOLOR false_color.sh &
monitor $CH15 ch15.sh &
monitor $M1 m1.sh &
monitor $M2 m2.sh
# monitor $EMWIN emwin.sh
