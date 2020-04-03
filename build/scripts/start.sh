#!/bin/bash

while [[ "$#" -gt 0 ]]; do case $1 in
  -i|--install) install=true; shift;;
  -u|--uninstall) uninstall=true; shift;;
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
    export DATABASE_URL="mysql://admin:password@localhost/enms";
  elif [ "$database" = "pgsql" ]; then
    export DATABASE_URL="postgresql://admin:password@localhost:5432/enms"
  fi
  if [ "$install" = true ]; then
    if [ "$database" = "mysql" ]; then
      sudo apt install -y mysql-server python3-mysqldb
      sudo pip3 install mysqlclient
      sudo mysql -u root --password=password -e 'CREATE DATABASE enms;'
      sudo mysql -u root --password=password -e 'set global max_connections = 2000;'
      sudo mysql -u root --password=password -e "ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'password';"
    elif [ "$database" = "pgsql" ]; then
      sudo apt-get install -y postgresql libpq-dev
      sudo pip3 install psycopg2
      sudo -u postgres psql -c "CREATE DATABASE enms;"
      sudo -u postgres psql -c "CREATE USER admin WITH PASSWORD 'password';"
      sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE enms TO admin;"
    fi
  elif [ "$reload" = true ]; then
    if [ "$database" = "mysql" ]; then
      sudo mysql -u root --password=password -e "DROP DATABASE enms;CREATE DATABASE enms;"
    elif [ "$database" = "pgsql" ]; then
      sudo -u postgres psql -c "DROP DATABASE enms;CREATE DATABASE enms;"
    else
      rm database.db
    fi
  elif [ "$uninstall" = true ]; then
    if [ "$database" = "mysql" ]; then
      sudo apt-get -y remove --purge "mysql*"
    elif [ "$database" = "pgsql" ]; then
      sudo apt-get --purge remove postgresql postgresql-client
      sudo rm -rf /var/lib/postgresql/
      sudo rm -rf /var/log/postgresql/
      sudo rm -rf /etc/postgresql/
    fi
    sudo apt-get -y autoremove
    sudo apt-get -y autoclean
    exit 0
  fi
  gunicorn --config gunicorn.py app:app
}

start;
