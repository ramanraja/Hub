# Activate module template, configure MQTT and turn on Wemo emulation on Tasmota
# NOTE: for some reason, Philips Hue emulation no longer works. But Wemo can support multiple devices now.
# After enabling emulation, tell Alexa to 'discover new devices'.

# Web server commands to Tasmota (Remember to url-encode them):
# http://192.168.4.1/wi?s1=ssid1&p1=pass1&s2=ssid2&p2=pass2&save=   # configure wifi
# http://192.168.0.14/cm?cmnd=mqtthost+192.168.0.100                # configure mqtt
# http://192.168.0.14/cm?module+0                                   # activate the hard-coded template found in the src code
# http://192.168.0.14/cm?restart+1                                  # restart tasmota

# Online URL encoder:
# https://www.urlencoder.org/

import sys
import json
import requests
from time import sleep

file = None
MAX_ATTEMPTS = 7
DELAY_SEC = 5
CONFIG_FILE = 'config.txt'
LOG_FILE = 'log.txt'
WIFI_TEMPLATE_FILE = 'wifi_profile_template.xml'  # TODO: implement this feature

tasmota_ip = "192.168.4.1"   # default address of a new Tasmota device
cmd_url  = None   
wifi_url = None 
enable_wifi_config = True

tasmota_config_AP = 'aaaa'   # TODO: implement connecting to this AP

ssid1 = None
ssid2 = None
passwd1 = None
passwd2 = None
hub_ip = None
friendly_names = []
security_key = None  # TODO: implement this

def dprint (*args):
    print (*args)
    log_entry = ' '.join([str(x) for x in args]) + '\n'
    file.write (log_entry)
    
def print_config ():
    dprint ('\nConfiguration:')
    dprint ('SSID1: ', ssid1)
    dprint ('SSID2: ', ssid2)
    dprint ('HUB IP: ', hub_ip)
    for i in range (len (friendly_names)):
        if len(friendly_names[i])==0:
            break       # you cannot skip any relay and assign a name to the next one
        dprint ('Alexa name {} : {}'. format(i+1, friendly_names[i]))
    dprint ('secret str lengths: ',len(passwd1),len(passwd2),len(security_key))
    
def read_config ():
    global enable_wifi_config, ssid1, ssid2, passwd1, passwd2, hub_ip, friendly_names, security_key
    dprint ('reading {}..'.format(CONFIG_FILE))
    try:
        jconf = None
        with open (CONFIG_FILE) as infile:
            jconf = json.load (infile)
        if (jconf is None):
            dprint ('ERROR: Cannot read config file')
            return False
        ssid1  = jconf.get ('wifi_ssid1') or ''
        passwd1 = jconf.get ('wifi_password1') or ''  
        ssid2 = jconf.get ('wifi_ssid2') or ''  
        passwd2 = jconf.get ('wifi_password2') or '' 
        # leave all the 4 fields undefined, if you don't want to configure wifi credentials
        if (len(ssid1)==0 and len(passwd1)==0 and len(ssid2)==0 and len(passwd2)==0):
            enable_wifi_config = False
        hub_ip = jconf.get('hub_ip') or '192.168.0.100'
        # We will skip empty keys and assign Alexa names to relay1, relay2 etc in that order ***
        # for eg, if alexa_name1 is empty, but alexa_name2 and alexa_name3 are present, then the first two relays will get the names. 
        # So change your load wiring, if needed!
        for i in range(4):
            temp_name = jconf.get('alexa_name'+str(i+1)) or None
            if (temp_name is not None and len(temp_name) > 0):  
                friendly_names.append (temp_name)          
        security_key = jconf.get ('security_key') or '!CAUTION-DEFAULT-SECURITY-KEY!'
        print_config ()  
    except Exception as e:
        dprint ('\nException: Error reading config file - ',str(e))
        return False
    dprint ('\nConfiguration successfully read.')
    return True
    
def config_mqtt ():
    dprint ('\nConfiguring MQTT broker...')
    broker = "mqtthost {}".format(hub_ip)
    params = {"cmnd" : broker}
    dprint ('URL: '+cmd_url)
    dprint (params)
    success = False
    for i in range(MAX_ATTEMPTS):
        try :
            print ('\n{}) contacting IoT device...'.format(i+1))
            res = requests.get(cmd_url, params=params) 
            dprint()
            dprint (res.text)
            #if ('html' in res):  # success indicator?
            dprint ('Connected.')
            success = True
            break
        except Exception as e:
            dprint ('Exception: could not connect to device; ' + str(e))
            sleep(DELAY_SEC)
    dprint ('\nresult: MQTT configured = ' + str(success))
    dprint ()
    dprint ('-'*50)
    return success

# 'module 0' command enables the device template
def config_module ():
    dprint ('\nConfiguring Hardware module...')
    params = {"cmnd" : "module 0"}
    dprint ('URL: '+cmd_url)
    dprint (params)
    success = False
    for i in range(MAX_ATTEMPTS):
        try :
            print ('\n{}) contacting IoT device...'.format(i+1))
            res = requests.get(cmd_url, params=params) 
            dprint()
            dprint (res.text)
            dprint ('Connected.')
            success = True
            break
        except Exception as e:
            dprint ('Exception: could not configure module; ' + str(e))
            sleep(DELAY_SEC)
    dprint ('\nresult: Module configured = ' + str(success))
    dprint ()
    dprint ('-'*50)
    return success
    
# 'timers 1' command enables all the timers (the 'enable timers' check box on the timer page)
def enable_timers ():
    dprint ('\nEnabling timers...')
    params = {"cmnd" : "timers 1"}
    dprint ('URL: '+cmd_url)
    dprint (params)
    success = False
    for i in range(MAX_ATTEMPTS):
        try :
            print ('\n{}) contacting IoT device...'.format(i+1))
            res = requests.get(cmd_url, params=params) 
            dprint()
            dprint (res.text)
            dprint ('Connected.')
            success = True
            break
        except Exception as e:
            dprint ('Exception: could not enable timers; ' + str(e))
            sleep(DELAY_SEC)
    dprint ('\nresult: Timers enabled = ' + str(success))
    dprint ()
    dprint ('-'*50)
    return success
        
# Philips Hue emulation does not work recently; Alexa is unable to discover devices
# But Belkin wemo works for multiple devices now
def config_alexa():
    if len (friendly_names)==0:
        dprint ('\nNot enabling Alexa emulation.')     
        return False
        
    dprint ('\nConfiguring Alexa emulation...')
    # the strings, if present, are already verified to be non-null and have length > 0
    # NOTE: do NOT put quotes around the friendly name strings, even if they have multiple words!
    cmd_str = 'backlog friendlyname1 ' + friendly_names[0] 
    if len (friendly_names) > 1:
        cmd_str = cmd_str + ';friendlyname2 ' +friendly_names[1] 
    if len (friendly_names) > 2:
        cmd_str = cmd_str + ';friendlyname3 ' +friendly_names[2] 
    if len (friendly_names) > 3:
        cmd_str = cmd_str + ';friendlyname4 ' +friendly_names[3] 
    params = {"cmnd" : cmd_str}
    dprint ('URL: '+cmd_url)
    dprint (params)
    
    success = False
    for i in range(MAX_ATTEMPTS):
        try :
            print ('\n{}) contacting IoT device...'.format(i+1))
            res = requests.get(cmd_url, params=params) 
            dprint()
            dprint (res.text)
            dprint ('Connected.')
            ####success = True
            break
        except Exception as e:
            dprint ('Exception: could not setup friendly names; ' + str(e))
            sleep(DELAY_SEC)

    params = {"cmnd" : "emulation 1"}  # Belkin Wemo
    dprint ('URL: '+cmd_url)
    dprint (params)            
    for i in range(MAX_ATTEMPTS):
        try :
            print ('\n{}) contacting IoT device...'.format(i+1))
            res = requests.get(cmd_url, params=params) 
            dprint()
            dprint (res.text)
            dprint ('Connected.')
            success = True
            break
        except Exception as e:
            dprint ('Exception: could not configure Belkin emulation; ' + str(e))
            sleep(DELAY_SEC)
    dprint ('\nresult: Alexa configured = ' + str(success))
    dprint ()
    dprint ('-'*50)
    return success
        
def config_wifi ():
    if (not enable_wifi_config):
        dprint ('\nWiFi credentials missing. Not configuring Wifi.')
        return False
    dprint ('\nConfiguring Wifi...')
    params = {
        "s1" : ssid1,
        "p1" : passwd1,
        "s2" : ssid2,
        "p2" : passwd2,
        "save" : ""    
    } 
    # "h" : "My-Host-Name" is not necessary
    dprint ('URL: '+wifi_url)
    dprint (params)
    success = False
    for i in range(MAX_ATTEMPTS):
        try :
            print ('\n{}) contacting IoT device...'.format(i+1))
            res = requests.get(wifi_url, params=params) 
            dprint()
            print (res.text)  # large response text, so do not dprint
            #if ('html' in res.text):  # success indicator
            dprint ('Connected.')
            success = True
            break
        except Exception as e:
            dprint ('Exception: could not configure WiFi; ' + str(e))
            sleep(DELAY_SEC)
    dprint ('\nresult: Wifi configured = ' + str(success))
    dprint ()
    dprint ('-'*50)
    return success
            
# it may be already restarted by wifi setup, this is just for safety    
def restart_device ():
    dprint ('\nRestarting device...')
    params = {"cmnd" : "restart 1"}
    dprint ('URL: '+cmd_url)
    dprint (params)
    success = False
    for i in range(2):  
        try :
            print ('\n{}) contacting IoT device...'.format(i+1))
            res = requests.get(cmd_url, params=params) 
            dprint()
            dprint (res.text)
            #if ('html' in res):  # success indicator
            dprint ('Connected.')
            success = True
            break
        except Exception as e:
            print ('Exception: could not restart device; ' + str(e))
            sleep(0.5)
    dprint ('\nresult: Device restarted = ' + str(success))
    dprint ()
    dprint ('-'*50)
    return success
                
if (__name__ == '__main__'):
    print ('Usage: python config.py [device_IP_address]')
    print ('Opening log file...')
    file = open (LOG_FILE, 'wt')
    if (file is None):
        dprint ('ERROR: could not create log file.')
        sys.exit(1)    
    dprint ('Log file opened.')
    if (len (sys.argv) > 1):
        tasmota_ip = sys.argv[1]
    cmd_url  = "http://{}/cm".format (tasmota_ip)    
    wifi_url = "http://{}/wi".format (tasmota_ip)
    dprint ('Tasmota device IP :', tasmota_ip)
    if not read_config():
        dprint ('ERROR: could not read config.txt file.')
        file.flush()
        file.close()        
        sys.exit(1)
    config_mqtt()
    config_module()
    enable_timers()
    config_alexa()    
    config_wifi()
    restart_device() # not needed, but just in case
    file.flush()
    file.close() 
    # dprint() will longer work !
    print('\nConfiguration ompleted.\nPlease see log.txt file for issues, if any.')
    
    
    