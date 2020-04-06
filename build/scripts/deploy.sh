#!/bin/bash

function install() {
  if [ "$install" = "vault" ]; then
    sudo apt-get install -y unzip
    find . -iname "*zip" -exec unzip {} \;
    sudo ln -s ${path:-$PWD}/vault /usr/bin/vault
    sudo ln -s ${path:-$PWD}/consul /usr/bin/consul
  elif [ "$install" = "mysql" ]; then
    sudo apt install -y mysql-server python3-mysqldb
    sudo pip3 install mysqlclient
    sudo mysql -u root --password=password -e 'CREATE DATABASE enms;'
    sudo mysql -u root --password=password -e 'set global max_connections = 2000;'
  elif [ "$install" = "postgresql" ]; then
    sudo apt-get install -y postgresql libpq-dev postgresql-client
    sudo pip3 install psycopg2
    sudo -u postgres psql -c "CREATE DATABASE enms;"
    sudo -u postgres psql -c "CREATE USER root WITH PASSWORD 'password';"
    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE enms TO root;"
  elif [ "$install" = "enms" ]; then
    sudo apt-get install -y python3-pip sshpass npm
    for file in build/requirements/*; do pip3 install -r $file; done
    sudo npm install -g prettier eslint eslint-config-google
  fi
}

function uninstall() {
  if [ "$uninstall" = "vault" ]; then
    sudo rm /usr/bin/{vault,consul}
    rm vault consul
  elif [ "$uninstall" = "mysql" ]; then
    sudo apt-get -y remove --purge "mysql*"
  elif [ "$uninstall" = "postgresql" ]; then
    sudo apt-get -y --purge remove postgresql\* libpq-dev
  fi
  sudo apt-get -y autoremove
  sudo apt-get -y autoclean
}


function deploy() {
  cd ${path:-$PWD}
  if [[ -n "$install" ]]; then
    install
  elif [[ -n "$uninstall" ]]; then
    uninstall
  fi
}

function help() {
  echo "
    Usage: $(basename $0) [OPTIONS]

    Options:
      -h                           Help
      -i <program>                 Install
      -p <path>                    Path to folder (default: current folder \$PWD)
      -u <program>                 Uninstall

    Programs:
      MySQL / PostgreSQL
      Vault
      eNMS (git, pip, requirements)
      Nginx
  "
  exit 0
}

while getopts h?p:i:u: opt; do
    case "$opt" in
      i) install=${OPTARG,,};;
      p) path=$OPTARG;;
      u) uninstall=${OPTARG,,};;
      h|\?) help;;
    esac
done

deploy
