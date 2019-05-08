# DistributedNetworkCameraCrawler

This system will allow security cameras on a network to communicate when another camera should expect an individual and raise an alert if the expectations are not met.

## Setup:
There two main ways this system can be setup.
1) Using the configs.cfg file and builddirs command
2) Individual directories with separate configurations all build independently

Using configs.cfg allows the user to set up multiple camera's in one file, then use the builddirs command to use that information to build a new directory with the appropriate settings for each client/alertServer.
To use the config.cfg, each each setting is defined as:
key:value
empty lines and lines starting with a # are ignored, so # comments can be used and spacing can be used to enhance readability.
The first two lines should be:
```
server_ip='ip address of the server'
server_port=server port
```
so that each client can know the address of the alert server.

The following line instructs `builddirs.sh` to make a directory for the alert server:

`server=alertServer`

Next, a list of cameras is defined by a tuple of IP addresses and ports. The list must exist between the lines `cameras=_` and `end_cameras=_` and each camera must be on its own line. For example:
```
cameras=_
client0=('192.168.1.3',51236)
client1=('192.168.1.4',51236)
client2=('192.168.1.5',51236)
client3=('192.168.1.6',51236)
end_cameras=_
```

After that each client is started by stating the name

`name=ClientName`

followed by a list of neighbors and whether or not it is an endpoint (e.g. door or other entry way). These can be specified in any order. The endpoints are written as Python boolean values (True/False). The neighbors list is a list of semicolon-separated tuples in the format (<camera_name>,side), where side is l or r.
For example:
```
name=client1
neighbors=(client0,l);(client2,r)
right_endpoint=False
left_endpoint=False
```


Once the configuration file is complete, simply running the `builddirs.sh` command will parse the configuration file and create directories with the required files. Each camera specified should then have its own directory with a copy of `client.py` and `camera.cfg`. The alert server directory should have those two files as well as `alertServer.py`.

If building `camera.cfg` files manually, they will look like this:
```
# Locate alert server
server_ip='ip address of the server'
server_port=<server_port>

# List all available cameras (or the ones necessary 
# for this camera to connect to)
client0=('192.168.1.3',51236)
client1=('192.168.1.4',51236)
client2=('192.168.1.5',51236)
client3=('192.168.1.6',51236)

# Define this camera and its settings
name=client1
neighbors=(client0,l);(client2,r)
right_endpoint=False
left_endpoint=True
```
## Running:
To run this system, the alert server must be started first. With all the configuration files set up, the alert server can be started via command line with `./alertServer`.

Once it is running, each client can be started in their respective directories in command line with `./client`.

The programs will read their configuration files to set themselves up and automatically connect to one another.

The main function in each client currently uses keyboard inputs, rather than automatic calls to notify appropriate peers of moving, missing, or unexpected objects. These will be replaced in future versions with automatic calls.

The current keyboard commands are:

>l=>object with ID 123 left this camera's field of view

>k=>object with ID 123 entered this camera's field of view

>r=>object with ID 234 left this camera's field of view

>e=>object with ID 234 entered this camera's field of view

>q=>quit

### Running with different triggers
To replace the manual keystrokes as triggers for users entering or leaving the screen, the detector must identify the individual with some unique integer and call the Client object's `left_screen_alert(<individual's_id>)` or `send_found_alert(<individual's_id>)` if a user left or entered the camera's view, respectively.
