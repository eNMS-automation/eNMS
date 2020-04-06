#!/bin/bash

function utils() {
  if [[ -n "$path" ]]; then cd $path; fi
  if [ "$install" = "vault" ]; then
    sudo apt-get install -y unzip
    find . -iname "vault_*zip" -exec unzip {} \;
    sudo ln -s $path/vault /usr/bin/vault
  elif [ "$uninstall" = "vault" ]; then
    sudo rm /usr/bin/vault && rm vault
  fi
}

function show_help() {
  echo help
  exit 0
}

while getopts h?u:i:p: opt; do
    case "$opt" in
      p) path=$OPTARG;;
      u) uninstall=$OPTARG;;
      i) install=$OPTARG;;
      h|\?) show_help;;
    esac
done

utils
