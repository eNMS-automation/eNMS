#!/bin/bash

while [[ "$#" -gt 0 ]]; do case $1 in
  -r|--reload-database) reload=true; shift;shift;;
  -p|--path) path="$2";shift;shift;;
  *) unknown=$1; shift; shift;;
esac; done

function start() {
  if [[ -n "$path" ]]
  then
    cd $path
  fi
  if [[ -n "$unknown" ]]
  then
   echo "Unknown parameter detected $unknown"
   exit 1
  fi
  FLASK_APP="app.py"
  FLASK_DEBUG=1
  if [ "$reload" = true ]
  then
    rm database.db
  fi
  gunicorn --config gunicorn.py app:app
}

start;
