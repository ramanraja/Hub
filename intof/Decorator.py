#  decorator for verifying the JWT token 

from flask import current_app as app  
from intof.Models import User
# from intof.HouseKeeper import dprint
# import intof.HouseKeeper as h
import jwt  # this is from PyJWT, not the plain jwt package *
from flask import request
from functools import wraps 

# will accept a cookie 'x-access-token' or a header 'x-access-token',
# depending on the config item USE_AUTH_HEADER being false or true

TOKEN_ID = app.config['TOKEN_ID'] 
###current_user = 'Anonymous'

# Send the header {x-access-token : <token>} or set a cookie with x-access-token=<token}
def token_required (f): 
    @wraps (f) 
    def decorated (*args, **kwargs): 
        token = None
        # jwt is passed in a cookie named x-access-token
        if (app.config.get('USE_AUTH_HEADER')==False):  # explictly comparing with False is safer!
            token = request.cookies.get (TOKEN_ID)
        else:
            # jwt is passed in a request header named x-access-token
            token = request.headers.get (TOKEN_ID)
        if token is None:
            print ('Auth failed. Missing security token: {}'.format(TOKEN_ID)) 
            return  ({'result' : False, 'error' : 'missing security token'}, 401)
        try: 
            # decode the payload to fetch the current user
            decoded_token = jwt.decode (token, app.config.get('SECRET_KEY')) 
            print ('Decoded token: ', decoded_token)
            mail = decoded_token['email']
            current_user = User.query.filter_by (email=mail).first() 
        except Exception as e:
            print ('Exception: ', e) 
            return  ({'result' : False, 'error' : str(e)}, 401)
        if (current_user is None):    # will not normally reach here, but the user may have got deleted after logging in
            return  ({'result' : False, 'error' : 'invalid or expired token'}, 401)
        # returns the current user's context to the routes 
        return f (current_user, *args, **kwargs) 
    return decorated 

    