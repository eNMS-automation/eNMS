#!/bin/bash

function utils() {
  cd ${path:-$PWD}
  if [ "$install" = "vault" ]; then
    sudo apt-get install -y unzip
    find . -iname "vault_*zip" -exec unzip {} \;
    sudo ln -s ${path:-$PWD}/vault /usr/bin/vault
  elif [ "$uninstall" = "vault" ]; then
    sudo rm /usr/bin/vault && rm vault
  fi
}

function show_help() {
  help="
    Usage: $(basename $0) [OPTIONS]

    Options:
      -p <path>                    Path to folder (default: current folder \$PWD)
      -i <program>                 Install program (Vault, TACACS+, ...)
      -u <program>                 Uninstall program
      -h                           Help
  "
  echo "$help"
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
