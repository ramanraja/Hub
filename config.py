import os
        
class Config (object):
    SIMULATION_MODE = False # True # 
    USE_AUTH_HEADER = True  # True=use header; False=use cookies
    TOKEN_ID = 'x-access-token'
    APP_PORT = os.environ.get ('APP_PORT') or 5000
    TEMPLATES_AUTO_RELOAD = True    
    HUB_ID = os.environ.get('HUB_ID') or 'Intof_Hub1.0'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///Hub.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO= False  # enable this to see the internal queries
    SECRET_KEY = os.environ.get ('SECRET_KEY') or '!default--secret-key!'
    
    MQTT_BROKER_URL = 'localhost'      
    MQTT_BROKER_PORT = 1883
    MQTT_KEEPALIVE = 60  # sec
    MQTT_TLS_ENABLED = False  
    LWT_TOPIC = 'tele/+/LWT'
    SUB_TOPIC = 'stat/#'         
    PUB_PREFIX = 'cmnd'
    PUB_SUFFIX = 'POWER'   
        
    CLIENT_EVENT = 'client-event'
    SERVER_EVENT = 'server-event'
    ACK_EVENT = 'ACK'
    BROADCAST_DEVICE = 'tasmotas'  # this is case sensitive *
    BROADCAST_RELSEN = 'POWER0'    # gets status of all the relays in a device 
    
    SENSOR_RELSEN = 'SENSOR'       # every device has a single relsen_id for all sensors combined
    SENSOR_SUFFIX = 'status'       # to read sensors: cmnd/device_id/status with a payload of '10'
    SENSOR_PAYLOAD = '10'  
    SENSOR_STATUS = 'STATUS10'     # device responds on the topic stat/device_id/STATUS10
    
    IPMAC_SUFFIX = 'status'        # to get network params: cmnd/device_id/status with a payload of '5'
    IPMAC_PAYLOAD = '5'  
    IPMAC_STATUS = 'STATUS5'
    
    PING_INTERVAL = 30             # daemon thread wake up interval, in seconds
    SENSOR_INTERVAL = 10           # sensor reading interval, in units of PING_INTERVAL (10 x 30 sec= 5 minutes)
    DPRINT_ENABLED = True          # debug printing
    
    def dump ():   # satic method
        print ('\nConfig:') 
        print ('SIMULATION_MODE: %s' % Config.SIMULATION_MODE)    
        if Config.USE_AUTH_HEADER: 
            print ('Using HTTP header for authentication')
        else:
            print ('Using cookies for authentication')
        print ('TOKEN_ID: %s' % Config.TOKEN_ID)
        print ('HUB_ID: %s' % Config.HUB_ID)
        print ('DATABASE_URI: %s' % Config.SQLALCHEMY_DATABASE_URI)
        print ('DPRINT_ENABLED: %s' % Config.DPRINT_ENABLED)
        print ('APP_PORT: %d [%s]' %(Config.APP_PORT, type(Config.APP_PORT)))
        print ('SECRET_KEY: %s' %'*****')  # Config.SECRET_KEY)
        print ('MQTT_BROKER_URL: %s' % Config.MQTT_BROKER_URL)         
        print ('MQTT_BROKER_PORT: %s' % Config.MQTT_BROKER_PORT)         
        print ('MQTT_KEEPALIVE: %d' % Config.MQTT_KEEPALIVE)   
        print ('SUB_TOPIC: %s' % Config.SUB_TOPIC)  
        print ('PUB_PREFIX: %s' % Config.PUB_PREFIX)         
        print ('PUB_SUFFIX: %s' % Config.PUB_SUFFIX) 
        print ('CLIENT_EVENT: %s' % Config.CLIENT_EVENT)          
        print ('SERVER_EVENT: %s' % Config.SERVER_EVENT)          
        print ('ACK_EVENT: %s' % Config.ACK_EVENT)    
        print ('PING_INTERVAL: %s' % Config.PING_INTERVAL)    
        print ('BROADCAST_DEVICE: %s' % Config.BROADCAST_DEVICE)    
        print ('BROADCAST_RELSEN: %s' % Config.BROADCAST_RELSEN)
        print ('SENSOR_RELSEN: %s' % Config.SENSOR_RELSEN)
        print ('SENSOR_STATUS: %s' % Config.SENSOR_STATUS)
        print ('SENSOR_SUFFIX: %s' % Config.SENSOR_SUFFIX)
        print ('SENSOR_PAYLOAD: %s' % Config.SENSOR_PAYLOAD)
        print ('IPMAC_STATUS : %s' % Config.IPMAC_STATUS)
        print ('IPMAC_SUFFIX: %s' % Config.IPMAC_SUFFIX)
        print ('IPMAC_PAYLOAD: %s' % Config.IPMAC_PAYLOAD)        
        print()        
        
'''-------------------------------------------------------------------------------------------------
stat/portico/STATUS5 
{"StatusNET":
 {"Hostname":"portico-7104","IPAddress":"192.168.0.10","Gateway":"192.168.0.1","Subnetmask":"255.255.255.0",
 "DNSServer":"103.99.150.10","Mac":"2C:F4:32:17:3B:C0","Webserver":2,"WifiConfig":4,"WifiPower":17.0}}
-------------------------------------------------------------------------------------------------'''        