#!/bin/bash

function start() {
  FLASK_APP="app.py"
  FLASK_DEBUG=1
  cd /media/sf_shared/eNMS/
  gunicorn --config gunicorn.py app:app
}

function usage() {
  if [ -n "$1" ]; then
    echo -e "${RED}👉 $1${CLEAR}\n";
  fi
  echo "Usage: $0 [-n number-of-people] [-s section-id] [-c cache-file]"
  echo "  -n, --number-of-people   The number of people"
  echo "  -s, --section-id         A sections unique id"
  echo "  -q, --quiet              Only print result"
  echo ""
  echo "Example: $0 --number-of-people 2 --section-id 1 --cache-file last-known-date.txt"
  exit 1
}

# parse params
while [[ "$#" > 0 ]]; do case $1 in
  -r|--reload-database) RELOAD=true; shift;shift;;
  *) usage "Unknown parameter passed: $1"; shift; shift;;
esac; done

echo $RELOAD;

# verify params
if [ "$RELOAD" = true ];
then
  start;
else
  start;
fi;
