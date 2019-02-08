#!/bin/bash

CONFIG=configs.cfg
CAM_CONFIG=camera.cfg
IFS="="
CAMERA_CLIENT_PY=camera_client.py

camName=""


while read -r key val
do
    echo "$key -> $val"
    if [ "$key" = "name" ]
    then
        mkdir $val
        cp ./$CAMERA_CLIENT_PY $val
        camName=$val
        echo "name=$val" > $val/$CAM_CONFIG
        
    elif [ "$key" = "left" ]
    then
        echo "left=$val" >> $camName/$CAM_CONFIG
    elif [ "$key" = "right" ]
    then
        echo "right=$val" >> $camName/$CAM_CONFIG
    fi
done < $CONFIG
