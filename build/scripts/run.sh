#!/bin/bash

function help() {
  echo "
    Usage: $(basename $0) [OPTIONS]

    Options:
      -d <database>                Database (mysql | pgsql | sqlite) (default: sqlite)
      -g                           Start the application with gunicorn
      -h                           Help
      -p <path>                    Path to folder (default: current folder \$PWD)
      -r                           Reload Database
      -q                           Use a redis queue
      -s                           Start scheduler
  "
  exit 0
}

function run() {
  if [[ -n "$path" ]]; then cd $path; fi
  if [ "$scheduler" = true ]; then
    cd scheduler
    export ENMS_ADDR="http://192.168.56.102"
    export ENMS_USER="admin"
    export ENMS_PASSWORD="admin"
    gunicorn --config gunicorn.py scheduler:scheduler
    exit 0
  fi
  if [ "$redis" = true ]; then
    export REDIS_ADDR="192.168.56.103"
  fi
  export SCHEDULER_ADDR="http://192.168.56.103:5000"
  export LDAP_ADDR="192.168.56.104"
  export TACACS_ADDR="192.168.56.104"
  export TACACS_PASSWORD="testing123"
  export FLASK_APP="app.py"
  export FLASK_DEBUG=1
  if [ "$database" = "mysql" ]; then
    export DATABASE_URL="mysql://root:password@localhost/enms";
  elif [ "$database" = "pgsql" ]; then
    export DATABASE_URL="postgresql://root:password@localhost:5432/enms"
  else
    export DATABASE_URL="sqlite:///database.db"
  fi
  if [ "$reload" = true ]; then
    if [ "$database" = "mysql" ]; then
      sudo mysql -u root --password=password -e "DROP DATABASE enms;CREATE DATABASE enms;"
    elif [ "$database" = "pgsql" ]; then
      sudo -u postgres psql -c "DROP DATABASE enms"
      sudo -u postgres psql -c "CREATE DATABASE enms;"
    else
      rm database.db
    fi
  fi
  if [ "$gunicorn" = true ]; then
    gunicorn --config gunicorn.py app:app
  else
    flask run -h 0.0.0.0
  fi
}

while getopts h?grqstvp:d: opt; do
    case "$opt" in
      d) database=$OPTARG;;
      g) gunicorn=true;;
      p) path=$OPTARG;;
      r) reload=true;;
      q) redis=true;;
      s) scheduler=true;;
      h|\?) help;;
    esac
done

run
