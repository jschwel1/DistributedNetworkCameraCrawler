#!/bin/bash

CONFIG=configs.cfg
IFS="="
CAMERA_CLIENT_PY=camera_client.py



while read -r key val
do
    if [ "$key" = "name" ]
    then
        echo "Removing $val directory recursively"
        rm -r $val
    fi

done < $CONFIG
