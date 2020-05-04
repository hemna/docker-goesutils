#!/bin/bash

TZ_NY=":US/Eastern"
TZ_LA=":US/Western"
TZ_GMT="GMT"

# This is sourced from lib.sh
BASE_DIR="/home/goes/data"
PROCESS_DIR="$BASE_DIR/processed"

GOESDATA="/home/goes/data"
FALSECOLOR="$GOESDATA/goes16/fd/$TODAY/false-color/"
CH15="$GOESDATA/goes16/fd/$TODAY/ch15_enhanced/"
M1="$GOESDATA/goes16/m1/$TODAY/ch13_enhanced"
M2="$GOESDATA/goes16/m2/$TODAY/ch13_enhanced"
EMWIN="$GOESDATA/emwin/$TODAY/"

# FD false-color defines
FC_DIR="$PROCESS_DIR/fd/$TODAY/false-color"
FC_VA="$FC_DIR/va"
FC_CA="$FC_DIR/ca"

# FD Channel 15 defines
CH15_DIR="$PROCESS_DIR/fd/$TODAY/ch15"
CH15_VA="$CH15_DIR/va"
CH15_CA="$CH15_DIR/ca"

# M1 channel
M1_DIR="$PROCESS_DIR/m1/$TODAY"

# M2 channel
M2_DIR="$PROCESS_DIR/m2/$TODAY"
