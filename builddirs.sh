#!/bin/bash

CONFIG=configs.cfg
CAM_CONFIG=camera.cfg
IFS="="
CAMERA_CLIENT_PY=camera_client.py

camName=""
serverIP=""
serverPort=""

while read -r key val
do
    echo "$key -> $val"
    # Trim key and val
    key=$(echo "$key" | xargs)
    val=$(echo "$val" | xargs)
    if [ "$key" = "server_ip" ]
    then
        serverIP=$val
    elif [ "$key" = "server_port" ]
    then
        serverPort=$val
    elif [ "$key" = "name" ]
    then
        camName=$val
        mkdir $camName
        cp ./$CAMERA_CLIENT_PY $camName
        echo "server_ip=$serverIP" > $camName/$CAM_CONFIG
        echo "server_port=$serverPort" >> $camName/$CAM_CONFIG
        echo "name=$camName" >> $camName/$CAM_CONFIG
        
    elif [ "$key" = "left" ]
    then
        echo "left=$val" >> $camName/$CAM_CONFIG
    elif [ "$key" = "right" ]
    then
        echo "right=$val" >> $camName/$CAM_CONFIG
    fi
done < $CONFIG
