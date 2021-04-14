Intof IoT Hub
 
New in this version: 
Offline operation of relays: the command is queued in last_known_good status and executed when the device comes online

If the number of socket clients connecting to the server automatically keeps increasing:
   An exception occurred, most probably within buttons.html. This crashes the socket connection but it automatically
   keeps trying to reestablish the connection.
   
If you encounter the error:
AttributeError: module 'jwt' has no attribute 'encode'     
pip uninstall JWT 
pip uninstall PyJWT 
pip install PyJWT. 
