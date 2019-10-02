#!/usr/bin/env bash

telegraf --config /etc/telegraf/telegraf.conf --quiet &

echo "using $CONF"
cd $HOME/bin
./monitor.sh
