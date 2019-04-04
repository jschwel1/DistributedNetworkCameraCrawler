# DistributedNetworkCameraCrawler

This system will allow security cameras on a network to communicate when another camera should expect an individual and raise an alert if the expectations are not met.

##Setup:
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
After that each client is started by stating the name
name=ClientName
followed by a list of neighbors, whether or not it is an endpoint (e.g. door or other entry way) and the port and ip it will be listening on. These can be specified in any order. The endpoints are just boolean values. The neighbors list is a list of semicolon-separated 3-tuples in the format (ip,port,side), where side is l or r.
For example:
```
name=Client1
neighbors=(127.0.0.1,51239,l);(127.0.0.1,51237,r)
right_endpoint=False
left_endpoint=False
listen_port=51236
listen_ip=127.0.0.1
```
In order to make a directory for the alert server, simply use the line:server=alertServerName

Once the configuration file is complete, simply running the builddirs.sh command will parse the configuration file and create directories with the required files.


##Running:
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
