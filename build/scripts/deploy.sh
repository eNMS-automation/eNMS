#!/bin/bash

function install() {
  if [ "$vault" = true ]; then
    sudo apt-get install -y unzip
    find . -iname "vault_*zip" -exec unzip {} \;
    sudo ln -s ${path:-$PWD}/vault /usr/bin/vault
  fi
  if [[ -n "$database" ]]; then
    if [ "$database" = "mysql" ]; then
      sudo apt install -y mysql-server python3-mysqldb
      sudo pip3 install mysqlclient
      sudo mysql -u root --password=password -e 'CREATE DATABASE enms;'
      sudo mysql -u root --password=password -e 'set global max_connections = 2000;'
    elif [ "$database" = "pgsql" ]; then
      sudo apt-get install -y postgresql libpq-dev postgresql-client
      sudo pip3 install psycopg2
      sudo -u postgres psql -c "CREATE DATABASE enms;"
      sudo -u postgres psql -c "CREATE USER root WITH PASSWORD 'password';"
      sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE enms TO root;"
    fi
  fi
}

function uninstall() {
  if [ "$vault" = true ]; then
    sudo rm /usr/bin/vault && rm vault
  fi
  if [[ -n "$database" ]]; then
    if [ "$database" = "mysql" ]; then
      sudo apt-get -y remove --purge "mysql*"
    elif [ "$database" = "pgsql" ]; then
      sudo apt-get -y --purge remove postgresql\* libpq-dev
    fi
    sudo apt-get -y autoremove
    sudo apt-get -y autoclean
    exit 0
  fi
}

function help() {
  echo "
    Usage: $(basename $0) [OPTIONS]

    Options:
      -d <database>                Database (mysql | pgsql)
      -h                           Help
      -i                           Install
      -p <path>                    Path to folder (default: current folder \$PWD)
      -u                           Uninstall
      -v                           Vault
  "
  exit 0
}

while getopts h?p:d:uiv opt; do
    case "$opt" in
      d) database=$OPTARG;;
      i) function=install;;
      p) path=$OPTARG;;
      u) function=uninstall;;
      v) vault=true;;
      h|\?) help;;
    esac
done

function deploy() {
  cd ${path:-$PWD}
  if [ "$function" = "install" ]; then
    install
  elif [ "$function" = "uninstall" ]; then
    uninstall
  fi
}

deploy
