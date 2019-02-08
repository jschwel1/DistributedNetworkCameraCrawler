#!/bin/bash

CONFIG=configs.cfg
IFS="="
CAMERA_CLIENT_PY=camera_client.py



while read -r key val
do
    # Trim key and val
    key=$(echo "$key" | xargs)
    val=$(echo "$val" | xargs)

    if [ "$key" = "name" ]
    then
        echo "Removing $val directory recursively"
        rm -r $val
    fi

done < $CONFIG
