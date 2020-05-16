#!/bin/bash

function help() {
  echo "
    Usage: $(basename $0) [OPTIONS]

    Options:
      -i                            Install
      -r                            Remove
      -u                            Update
      -p <plugin>                   Plugin Name

      List of available plugins:
        - plugin-template (serves as a template for creating a plugin)
  "
  exit 0
}

function run() {
  if [[ -z "$plugin" ]]; then
    echo "No plugin specified";
    exit 1;
  fi
  cd eNMS/plugins
  if [ "$mode" = "update" ]; then
    cd $plugin
    git pull
  elif [ "$mode" = "remove" ]; then
    rm -r $plugin
  else
    git clone git@github.com:eNMS-automation/$plugin.git
  fi
}

while getopts h?irup: opt; do
    case "$opt" in
      p) plugin=$OPTARG;;
      i) mode="install";;
      r) mode="remove";;
      u) mode="update";;
      h|\?) help;;
    esac
done

run
