#!/bin/bash

function help() {
  echo "
    Usage: $(basename $0) [OPTIONS]

    Options:
      -i                            Install
      -r                            Remove
      -u                            Update
      -p <plugin>                   Plugin Name
  "
  exit 0
}

function run() {
  if [ "$mode" = "install" ]; then
    echo "install"
  elif [ "$mode" = "remove" ]; then
    echo "remove"
  else
    echo "update"
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
