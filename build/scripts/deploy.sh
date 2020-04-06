#!/bin/bash

function install() {
  if [[ -n "$vault" ]]; then
    sudo apt-get install -y unzip
    find . -iname "vault_*zip" -exec unzip {} \;
    sudo ln -s ${path:-$PWD}/vault /usr/bin/vault
  fi
}

function uninstall() {
  if [[ -n "$vault" ]]; then
    sudo rm /usr/bin/vault && rm vault
  fi
}

function help() {
  echo "
    Usage: $(basename $0) [OPTIONS]

    Options:
      -p <path>                    Path to folder (default: current folder \$PWD)
      -i | -u                      Install or uninstall programs.
      -v                           Vault
      -h                           Help
  "
  exit 0
}

while getopts h?p:uiv opt; do
    case "$opt" in
      p) path=$OPTARG;;
      u) function=uninstall;;
      i) function=install;;
      v) vault=1;;
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
