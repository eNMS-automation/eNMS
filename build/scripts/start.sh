#!/bin/bash

while [[ "$#" -gt 0 ]]; do case $1 in
  -r|--reload) reload=true; shift;;
  -p|--path) path="$2"; shift;shift;;
  -d|--database) database="$2"; shift;shift;;
  *) unknown=$1; shift; shift;;
esac; done

function start() {
  if [[ -n "$path" ]]; then cd $path; fi
  if [[ -n "$unknown" ]]; then echo "Unknown parameter $unknown"; exit 1; fi
  export FLASK_APP="app.py"
  export FLASK_DEBUG=1
  if [ "$database" = "mysql" ]; then
    export DATABASE_URL="mysql://root:password@localhost/enms";
  elif [ "$database" = "pgsql" ]; then
    export DATABASE_URL="postgresql://root:password@localhost:5432/enms"
  else
    export DATABASE_URL="sqlite:///database.db"
  fi
  elif [ "$reload" = true ]; then
    if [ "$database" = "mysql" ]; then
      sudo mysql -u root --password=password -e "DROP DATABASE enms;CREATE DATABASE enms;"
    elif [ "$database" = "pgsql" ]; then
      sudo -u postgres psql -c "DROP DATABASE enms"
      sudo -u postgres psql -c "CREATE DATABASE enms;"
    else
      rm database.db
    fi
  gunicorn --config gunicorn.py app:app
}

start
