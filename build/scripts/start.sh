#!/bin/bash

while [[ "$#" -gt 0 ]]; do case $1 in
  -r|--reload) reload=true; shift;;
  -p|--path) path="$2"; shift;shift;;
  -d|--database) database="$2"; shift;shift;;
  -c|--create) create=true; shift;;
  *) unknown=$1; shift; shift;;
esac; done

function start() {
  if [[ -n "$path" ]]; then cd $path; fi
  if [[ -n "$unknown" ]]; then echo "Unknown parameter$unknown"; exit 1; fi
  FLASK_APP="app.py"
  FLASK_DEBUG=1
  if [ "$database" = "mysql" ]; then
    DATABASE_URL="mysql://root:enms@localhost/enms";
  fi
  if [ "$reload" = true ]; then
    if [ "$database" = "mysql" ]; then
      sudo mysql -u root -p -e "DROP DATABASE enms;CREATE DATABASE enms;"
    else
      rm database.db;
    fi
  fi
  if [ "$create" = true ] && [ "$database" = "mysql" ]; then
    sudo mysql -u root -p "enms" -e "CREATE DATABASE enms;"
    sudo mysql -u root -p "enms" -e "set global max_connections = 2000;"
    sudo mysql -u root -p "enms" -e "ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'enms';"
  fi
  #gunicorn --config gunicorn.py app:app
}

start;
