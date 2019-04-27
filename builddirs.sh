#!/bin/bash

CONFIG=configs.cfg
CAM_CONFIG=camera.cfg
IFS="="
CAMERA_CLIENT_PY=client.py

ALERT_SERVER_PY=alertServer.py

TEMP_FILE_FOR_CAMERAS=tempCameralist

camName=""
serverIP=""
serverPort=""

# Setup Alert server
#mkdir $ALERT_SERVER_DIR
#echo "name=$ALERT_SERVER_NAME" > $ALERT_SERVER_DIR/$ALERT_SERVER_CONFIG
#cp $ALERT_SERVER_PY $ALERT_SERVER_DIR

# Clear temp file
echo "" > $TEMP_FILE_FOR_CAMERAS
listofcameras="f"
while read -r key val
do
    echo "$key -> $val"
    # Trim key and val
    key=$(echo "$key" | xargs)
    val=$(echo "$val" | xargs)

    if [ $listofcameras = "t" ]
    then 
        if [ "$key" = "end_cameras" ]
        then
            listofcameras="f"
        else
            echo "$key=$val" >> $TEMP_FILE_FOR_CAMERAS
        fi
        continue
    fi

    if [ "$key" = "server_ip" ]
    then
        serverIP=$val
    elif [ "$key" = "server_port" ]
    then
        serverPort=$val
    elif [ "$key" = "cameras" ]
    then
        listofcameras="t"
    elif [ "$key" = "name" ]
    then
        camName=$val
        mkdir $camName
        cp ./$CAMERA_CLIENT_PY $camName
        echo "server_ip=$serverIP" > $camName/$CAM_CONFIG
        echo "server_port=$serverPort" >> $camName/$CAM_CONFIG
        echo "name=$camName" >> $camName/$CAM_CONFIG
        cat $TEMP_FILE_FOR_CAMERAS >> $camName/$CAM_CONFIG
    elif [ "$key" = "server" ]
    then
        camName=$val
        mkdir $camName
        cp ./$ALERT_SERVER_PY $camName
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
    elif [ "$key" = "" ]
    then
        echo ""
    else
        echo "$key=$val" >> $camName/$CAM_CONFIG
    fi
done < $CONFIG
rm $TEMP_FILE_FOR_CAMERAS
