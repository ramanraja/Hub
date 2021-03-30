Intof IoT Hub
 
New in this version: 
Dynamic creation of socket buttons

If the number of socket clients connecting to the server automatically keeps increasing:
   An exception occurred, most probably within buttons.html. This crashes the socket connection but it automatically
   keeps trying to reestablish the connection.
   
If you encounter the error:
AttributeError: module 'jwt' has no attribute 'encode'    
Uninstall every  *JWT :
pip uninstall JWT 
pip uninstall PyJWT 

Again install PyJWT :
pip install PyJWT. 
