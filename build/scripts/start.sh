#!/bin/bash

while [[ "$#" -gt 0 ]]; do case $1 in
  -i|--install) install=true; shift;;
  -r|--reload) reload=true; shift;;
  -p|--path) path="$2"; shift;shift;;
  -d|--database) database="$2"; shift;shift;;
  *) unknown=$1; shift; shift;;
esac; done

function start() {
  if [[ -n "$path" ]]; then cd $path; fi
  if [[ -n "$unknown" ]]; then echo "Unknown parameter$unknown"; exit 1; fi
  export FLASK_APP="app.py"
  export FLASK_DEBUG=1
  if [ "$database" = "mysql" ]; then
    export DATABASE_URL="mysql://root:password@localhost/enms";
  elif [ "$database" = "pgsql" ]; then
    export DATABASE_URL="postgresql://root:password@localhost:5432/enms"
  fi
  if [ "$install" = true ]; then
    if [ "$database" = "mysql" ]; then
      sudo apt install -y mysql-server python3-mysqldb
      sudo pip3 install mysqlclient
      sudo mysql -e "CREATE DATABASE enms;"
      sudo mysql -e "set global max_connections = 2000;"
      sudo mysql -e "ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'password';"
    elif [ "$database" = "pgsql" ]; then
      sudo apt-get install -y postgresql libpq-dev
      sudo pip3 install psycopg2
      sudo -u postgres psql -c "CREATE DATABASE enms;"
      sudo -u postgres psql -c "CREATE USER root WITH PASSWORD 'password';"
      sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE enms TO root;"
    fi
  fi
  if [ "$reload" = true ]; then
    if [ "$database" = "mysql" ]; then
      sudo mysql -u root -p -e "DROP DATABASE enms;CREATE DATABASE enms;"
    elif [ "$database" = "pgsql" ]; then
      sudo -u postgres psql -c "DROP DATABASE enms;CREATE DATABASE enms;"
    else
      rm database.db
    fi
  fi
  gunicorn --config gunicorn.py app:app
}

start;
