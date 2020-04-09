#!/bin/bash

function help() {
  echo "
    Usage: $(basename $0) [OPTIONS]

    Options:
      -d <database>                Database (mysql | pgsql | sqlite) (default: sqlite)
      -h                           Help
      -p <path>                    Path to folder (default: current folder \$PWD)
      -r                           Reload Database
  "
  exit 0
}

function run() {
  if [[ -n "$path" ]]; then cd $path; fi
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
  if [ "$vault" = true ]; then
    export VAULT_ADDR=http://192.168.56.103:8200
    export VAULT_TOKEN=s.nxEFgvw0MINej8ESerFgChxv
    export UNSEAL_VAULT_KEY1=PI9A7c1zCPa9hbASCwbok0vfnwUerYSuS95uuhXRBYmn
    export UNSEAL_VAULT_KEY2=+aZzxLBLReCn/WWrWOE165GcdGCaPwu+sNvKxh+LnNe3
    export UNSEAL_VAULT_KEY3=Xhvs0EhNWfZUwXAJfayoVdcrD0yKVob+j5sErrs+LEkw
  fi
  if [ "$gunicorn" = true ]; then
    gunicorn --config gunicorn.py app:app
  else
    flask run -h 0.0.0.0
  fi
}

while getopts h?rvgp:d: opt; do
    case "$opt" in
      d) database=$OPTARG;;
      g) gunicorn=true;;
      p) path=$OPTARG;;
      r) reload=true;;
      v) vault=true;;
      h|\?) help;;
    esac
done

run
