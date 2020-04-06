#!/bin/bash

function install_vault() {
  echo installing vault
  
}

function show_help() {
  echo help
  exit 0
}

while getopts h?i: opt; do
    case "$opt" in
      i) if [ "$OPTARG" == "vault" ]; then install_vault; fi;;
      h|\?) show_help;;
    esac
done
