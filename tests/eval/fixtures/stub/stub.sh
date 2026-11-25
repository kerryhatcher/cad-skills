#!/bin/sh
# Local stub host for the adapter and isolation tests. It contacts no provider and no network.
# The loopback connect uses bash, and the test gives it a local listener only.
#
#   stub.sh                       prints its arguments and a done line
#   stub.sh --read PATH           reports whether PATH can be read (the boundary test)
#   stub.sh --sleep N             sleeps N seconds (the timeout test)
#   stub.sh --exit N              exits with N (the failure test)
#   stub.sh --spawn-child N       starts a child that appends a tick every 0.2 s to
#                                 proc/child-ticks.txt, then the parent sleeps N seconds
#   stub.sh --connect PORT        connects to 127.0.0.1:PORT from inside the process namespace
#   stub.sh --net-interfaces      lists the network interfaces visible to the process

case "$1" in
  --read)
    if cat "$2" >/dev/null 2>&1; then echo "read=yes"; else echo "read=no"; fi
    exit 0
    ;;
  --sleep)
    sleep "$2"
    echo "slept $2"
    exit 0
    ;;
  --exit)
    echo "exiting $2"
    exit "$2"
    ;;
  --spawn-child)
    mkdir -p /work/proc
    : > /work/proc/child-ticks.txt
    # The child writes one tick every 0.2 s until it is terminated.
    ( while true; do echo tick >> /work/proc/child-ticks.txt; sleep 0.2; done ) &
    echo "child started"
    sleep "$2"
    echo "parent finished"
    exit 0
    ;;
  --connect)
    if /bin/bash -c "exec 3<>/dev/tcp/127.0.0.1/$2" 2>/dev/null; then
      echo "connect=yes"
    else
      echo "connect=no"
    fi
    exit 0
    ;;
  --net-interfaces)
    tail -n +3 /proc/net/dev | cut -d: -f1 | tr -d ' '
    exit 0
    ;;
esac
echo "args: $*"
echo "done"
