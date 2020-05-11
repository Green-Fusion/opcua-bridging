# OPC-UA forwarding

We are interested in finding a way to remotely access one or many 
OPC-UA servers. 

Specifically we want to be able to have a middleman service between client and server which can provide up-to-date
information on all of the relevant variables on one or more servers. We would also like to be able to change parameters
on the server from the client, again via the middleware. 

Thanks to the hard work of the asyncua team at https://github.com/FreeOpcUa/opcua-asyncio 
this is possible in python. 

The OPC-UA standard indicates that the best way to do this is to have a process that acts as both a client to the server
and a server to the eventual end-client. We have this in `cloud/cloud/forwarding_service.py` which subscribes to the server
in `PLC/PLC` as a client and serves the changes to `client/client` as a server.

There is no client > PLC connection right now. That's a high priority here.

## Usage
For now, you can run the integration test with `make test`. If you want to try the OPC servers out (cloud and plc) then 
run `make up`. The PLC server is at `0.0.0.0:4840` and the cloud server is `0.0.0.0:4839`.
