from flask import current_app as app  # this is the way to import the app object
from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from random import randint
from datetime import datetime
import json
from intof import db
from intof.Models import Device, Relsen, Status
##from intof.Decorator import token_required # TODO: protect some of the APIs with authentication

#----------------------------------------------------------------------------------------
# Test
#----------------------------------------------------------------------------------------
def router_test_method():
    print ('\n--- I am the router stub ! ---\n')
        
#-----------------------------------------------------------------------------------------
# helper methods    
#-----------------------------------------------------------------------------------------

def build_device_details_tree():
    print ('stub')  # TODO: implement this
 
def build_constant_lists():  # retrieve room_types, relsen_types etc from DB and cache them
    print ('stub')  # TODO: implement this ? here ?
    
def build_device_relsen_tree (device): # input: a device object from the DB
    devid = device.device_id
    retval = {devid : []}
    for rs in device.relsens:
        retval[devid].append (rs.relsen_id)
    return retval
        
def build_relsen_ids_tree (relsens):   # input: a list of relsen objects in the DB
    retval = {} 
    for rs in relsens: 
        if rs.device_id not in retval:
            retval[rs.device_id] = []
        retval[rs.device_id].append (rs.relsen_id)
    return (retval)  

def build_active_relsen_ids_tree (relsens):   # input: a list of relsen objects in the DB
    retval = {} 
    for rs in relsens: 
        if (rs. controller.enabled==False):  
            continue     
        if rs.device_id not in retval:
            retval[rs.device_id] = []
        retval[rs.device_id].append (rs.relsen_id)
    return (retval)  
    
def build_relsen_details_tree (relsens): # input: a list of relsen objects
    retval = {} 
    for rs in relsens: 
        if rs.device_id not in retval:
            retval[rs.device_id] = []
        retval[rs.device_id].append (rs.toJSON())
    return (retval)  

def build_active_relsen_details_tree (relsens): # input: a list of relsen objects
    retval = {} 
    for rs in relsens: 
        if (rs. controller.enabled==False):   
            continue 
        if rs.device_id not in retval:
            retval[rs.device_id] = []
        retval[rs.device_id].append (rs.toJSON())
    return (retval)  
    
    
'''
TODO:  ***
the following function has a dummy implementation in HouseKeeper.
remove that, and implement the below funcation    
@app.route('/add/devices')   
def add_devices (wifi_ssid_list):      
    print ('STUB: add_devices')
'''
    
# Old design:
# A device is onboarded in the disable state; this is because: (1) we can find it later using get/new/devices,
#   so that we can configure it and (2) Relsens of the new device are not yet configured, so search by name/type/room etc will fail.
# When you subsequently call update_relsen, it automatically invokes enable_device()
# New design:
# onboard the devices in the enabled state. (1) get/new/devices now does not look for the enabled=False condition. (uses blank relsen names)
#(2) unconfigured devices need not, and cannot, appear in searche results
def onboard_device (jnew_device):
    dprint ('\nOnboarding: ', jnew_device)
    if  not insert_device (jnew_device['device_id']):
        return False
    for rsid in jnew_device['relsen_list']: 
        if not insert_relsen (jnew_device['device_id'], rsid):
            return False
    ###build_device_inventory()  # update in-mem structures; TODO: revisit this. needs testing. will this call succeed, since they are disabled?
    build_active_device_inventory_route()  # this initializes their status also
    return True 
    

# this is only a convenience method; the client should iterate through its list of devices and invoke
#  onboard_device() one by one; that will give feedback about which of the devices failed to onboard    
# jdevice_tree is the value returned from  /discover/devices  eg: {"coffee": ["POWER1", "POWER2"],..}
def bulk_onboard_devices (jdevice_tree):
    success = True
    for devid in jdevice_tree.keys():
        jnew_device = {'device_id':devid, 'relsen_list':jdevice_tree[devid]}
        if  not onboard_device (jnew_device):
            success = False # even if one of them fails, return false eventually
    ###build_device_inventory()  # update in-mem structures; TODO: revisit this. needs testing. will this call succeed, since they are disabled?
    build_active_device_inventory_route()  # this initializes their status also    
    return success  
    
# Note: A new device is enabled by default ***    
def insert_device (device_id, fallback_id=None, mac=None, ip=None, 
                hardware_type="Generic", num_relays=1, num_sensors=0, 
                enabled=True):
    if (not device_id or len(device_id)==0):
        dprint ('Invalid device_id')
        return False  # TODO: return the error reason also
    dprint ('inserting device id: {}'.format(device_id))
    # check for existing device (device_id must be unique)
    dev = Device.query.filter_by (device_id=device_id).first() 
    if dev: 
        dprint ('Device ID already exists: {}'.format(device_id))
        return False
    # check for existing device (fallback_id must be unique)
    if (fallback_id):
        fb = Device.query.filter_by (fallback_id=fallback_id).first() 
        if fb: 
            dprint ('Falback ID already exists: {}'.format(fallback_id))
            return False   
    dev = Device ( 
        device_id = device_id, 
        fallback_id = fallback_id, 
        mac = mac,
        ip = ip,
        hardware_type = hardware_type, 
        num_relays = num_relays,   
        num_sensors = num_sensors,
        enabled = enabled) 
    db.session.add (dev) 
    db.session.commit()   
    dprint ('Added device: {}'.format(dev))
    return True   
    
        
def update_device (jdevice):
    dprint ('updating: ', jdevice)
    device_id = jdevice.get('device_id') or None
    if (not device_id or len(device_id)==0):
        return ({'result' : False, 'error' : 'Invalid device_id'})
    dev = Device.query.filter_by (device_id=device_id).first() 
    if not dev: 
        return ({'result' : False, 'error' : 'device_id does not exist'})
    # TODO: keep the default fallback id of Tasmota as it is; do not change it!
    fallback_id =  jdevice.get ('fallback_id') or None
    # fallback_id must be a unique non-empty string
    if (fallback_id and len (fallback_id) > 0) : 
        fb = Device.query.filter_by (fallback_id=fallback_id).first() 
        if fb: 
            return ({'result' : False, 'error' : 'fallback_id already exists'})
        dev.fallback_id = fallback_id
    # TODO: keep the discovered MAC and IP of the device without changing
    mac = jdevice.get('mac') or None    
    if (mac): dev.mac = mac
    ip = jdevice.get('ip') or None    
    if (ip): dev.ip = ip
    hardware_type = jdevice.get('hardware_type') or None    
    if (hardware_type): dev.hardware_type = hardware_type
    # TODO: auto discover num_relays
    num_relays = jdevice.get('num_relays') or -1    
    if (num_relays >= 0): dev.num_relays = num_relays   
    # TODO: there is only one sensor object containing a JSON of all sensors
    num_sensors = jdevice.get('num_sensors') or -1    
    if (num_sensors >= 0): dev.num_sensors = num_sensors
    print(jdevice.get('enabled'))
    ####enab = jdevice.get('enabled') or None   # TODO: understand the if(None) behaviour of a boolean variable in python!
    if 'enabled' in jdevice:
         dev.enabled = jdevice.get('enabled') 
    db.session.commit()   
    return ({'result' : True, 'msg' : 'successfully updated device'})
 
 
def enable_device (device_id):
    if (device_id is None or len(device_id)==0):
        return ({'result' : False, 'error' : 'Invalid device_id'})
    dev = Device.query.filter_by (device_id=device_id).first() 
    if not dev: 
        return ({'result' : False, 'error' : 'device_id does not exist'})
    dev.enabled = True
    db.session.commit()   
    return ({'result' : True, 'msg' : 'successfully enabled device'})
    
    
def disable_device (device_id):
    if (not device_id or len(device_id)==0):
        return ({'result' : False, 'error' : 'Invalid device_id'})
    dev = Device.query.filter_by (device_id=device_id).first() 
    if not dev: 
        return ({'result' : False, 'error' : 'device_id does not exist'})
    dev.enabled = False
    db.session.commit()   
    return ({'result' : True, 'msg' : 'successfully disabled device'})    
    
    
def insert_relsen (device_id, relsen_id, 
                relsen_name=None, relsen_type=None, 
                room_name=None, room_type=None, group_name=None,
                schedule=None, repeat=False):
    dprint ('inserting relsen: {}:{}'.format (device_id, relsen_id))                
    # check for existance of device (device_id must preexist)
    dev = Device.query.filter_by (device_id=device_id).first() 
    if not dev: 
        dprint ('Unknown device ID: {}'.format(device_id))
        return False
    for rel in dev.relsens:  # combination of (device_id+relsen_id) must be unique
        if (rel.relsen_id==relsen_id):
            dprint ('{}.{} already exists'.format(device_id, relsen_id))
            return False
    rs = Relsen ( 
        controller = dev,
        relsen_id = relsen_id, 
        relsen_name = relsen_name,
        relsen_type = relsen_type,
        room_name = room_name,
        room_type = room_type,
        group_name = group_name,
        schedule = schedule,   # LHS is the DB column name; RHS is a stringified json object (which has 'schedule' as the key)
        repeat = repeat) 
    db.session.add (rs) 
    db.session.commit()    
    dprint ('Added relay: {}'.format(rs))
    return True   
    

def update_relsen (jrelsen):
    device_id = jrelsen.get('device_id') or None        
    if (not device_id or len(device_id)==0):
        return ({'result' : False, 'error' : 'Invalid device_id'})
    relsen_id = jrelsen.get('relsen_id') or None 
    if (not relsen_id or len(relsen_id)==0):
        return ({'result' : False, 'error' : 'Invalid relsen_id'})
    dev = Device.query.filter_by (device_id=device_id).first() 
    if not dev: 
        return ({'result' : False, 'error' : 'device_id does not exist'})
    rs = Relsen.query.filter_by (device_id=device_id, relsen_id=relsen_id).first() 
    if (not rs):
        return ({'result' : False, 'error' : 'relsen_id does not exist'})
    relsen_name = jrelsen.get('relsen_name') or None 
    if (relsen_name):  rs.relsen_name = relsen_name
    relsen_type = jrelsen.get('relsen_type') or None 
    if (relsen_type):  rs.relsen_type = relsen_type
    room_name = jrelsen.get('room_name') or None 
    if (room_name):  rs.room_name = room_name
    room_type = jrelsen.get('room_type') or None 
    if (room_type):  rs.room_type = room_type
    group_name = jrelsen.get('group_name') or None    
    if (group_name):  rs.group_name = group_name
    dprint ('incoming schedule: ', jrelsen.get('schedule'))
    schedule = jrelsen.get('schedule') 
    if (schedule is None):  # an empty array evaluates to False ***
        schedule = []
    dprint ('new schedule: ', schedule)
    dprint ('updating schedule..')
    rs.schedule = json.dumps ({'schedule' : schedule})   # store it as a stringified json (so, the 'schedule' key is again needed!)
    rs.repeat = False
    if 'repeat' in jrelsen:
         rs.repeat = jrelsen.get('repeat') 
    db.session.commit()    
    enable_device (device_id)  # if previously disabled, automatically enable it now
    if (schedule is not None and len(schedule) > 0):
        dprint ('sending schedule update to Tasmota..')
        update_timer (device_id, relsen_id, jrelsen.get('schedule'), rs.repeat)
    return ({'result' : True, 'msg' : 'successfully updated relsen'})
        
        
# quick and dirty test to determine if a relsen object has been configured        
def is_configured (relsen_obj):        
    if (relsen_obj.relsen_name is None or len(relsen_obj.relsen_name)==0):
        return False
    if (relsen_obj.room_name is None or len(relsen_obj.room_name)==0):
        return False
    return True


# TODO: this is defunct code now. To be implemented later when status is stored in DB *        
def insert_status (device_id, relay_status=None, sensor_values=None,    # time_stamp=None, 
                event_type=None, online=True): 
    return {'result' : True, 'msg' : 'this is a placeholder'}
    
    # check for existance of device (device_id must already exist)
    dev = Device.query.filter_by (device_id=device_id).first() 
    if not dev: 
        dprint ('Unknown device ID: {}'.format(device_id))
        return False
    st = Status ( 
        controller = dev,
        relay_status = relay_status,  
        sensor_values = sensor_values,
        event_type = event_type,
        online = online) 
    db.session.add (st) 
    db.session.commit()   
    dprint ('Added status: {}'.format(st))
    return True   
    
# NOTE: There is no need for update_status(). That will be based on MQTT events.

# Work flow:
# call /discover/wifi/devices. This returns a list of wireless AP names. 
# Select the devices you want to onboard and make a list.
# Pass that list to this function
@app.route('/add/devices', methods =['GET', 'POST'])   # TODO: this is a place holder for the actual add_devices
@app.route('/simul/add/devices', methods =['GET', 'POST'])  # TODO: decouple this for production !
def simul_add_devices():                               # TODO: implement the actual function (in Router.py, not here!) 
    if (request.method=='GET'):
        #return ({'result' : False, 'error':'POST the newly discovered devices as JSON list'})
        print ('Got a simple GET request without data.. Proceeding anyway..!')
    if (request.json is None or request.json.get('new_devices') is None):
        #return ({'result' : False, 'error':'invalid Device list'})
        print ('No device list received, proceeding with my own..!')
    else:
        print ('New Wifi device list (simulated) received:')
        print (request.json)
    print ('Simulating adding new wifi devices...')
    simul_bulk_onboard()
    return {'result' : True, 'msg' : 'Your new devices will be onboarded now. This may take several minutes'}
#----------------------------------------------------------------------------------------
# Upatates 
#----------------------------------------------------------------------------------------

@app.route ('/update/device', methods =['GET', 'POST'])
def update_device_route():
    if (request.method=='GET'):
        return ({'result' : False, 'error':'POST the new Device values as JSON'})
    if (not request.json):
        return ({'result' : False, 'error':'invalid Device data'})
    return (update_device(request.json))
    
    
@app.route('/update/relsen', methods =['GET', 'POST']) 
@app.route('/configure/relsen', methods =['GET', 'POST']) 
def update_relsen_route():
    if (request.method=='GET'):
        return ({'result' : False, 'error':'POST the new Relsen values as JSON'})
    if (not request.json):
        return ({'result' : False, 'error':'invalid Relsen data'})
    return (update_relsen(request.json))
    
#---------------------------------------------------------------------------------------------------
# dump
#---------------------------------------------------------------------------------------------------

#------------------------------------ All Devices ------------------------------------------------------
# only ids
@app.route('/get/devices', methods =['GET']) 
@app.route('/get/device/list', methods =['GET']) 
def list_all_devices(): 
    devs = Device.query.all()
    retval = [] 
    for d in devs: 
        retval.append(d.device_id) 
    return ({'devices': retval})     

# full dump of all devices, including associated relsens, as a list
@app.route('/dump/devices', methods =['GET']) 
def dump_all_devices(): 
    devs = Device.query.all()
    retval = [] 
    for d in devs: 
        retval.append(d.toJSON()) 
    return ({'devices': retval})  
        
# full dump of all devices, including associated relsens, as a tree
@app.route('/dump/device/tree', methods =['GET']) 
def dump_all_device_tree(): 
    devs = Device.query.all()
    retval = {} 
    for d in devs: 
        retval[d.device_id] = d.toJSON()
    return (retval) 
            
# config and technical specs as a list       
@app.route('/dump/device/specs', methods =['GET']) 
def dump_device_specs(): 
    devs = Device.query.all()
    retval = [] 
    for d in devs: 
        retval.append(d.get_device_specs())  
    return ({'devices': retval})

# config and technical specs as a tree            
@app.route('/dump/device/spec/tree', methods =['GET']) 
def dump_device_spec_tree(): 
    devs = Device.query.all()
    retval = {} 
    for d in devs: 
        retval[d.device_id] = (d.get_device_specs())  
    return (retval) 
                
#------------------------------------ Active/inactive Devices ---------------------------------

# only enabled device ids, from the database
@app.route('/get/active/devices', methods=['GET'])      
def get_active_devices():    
    devs = Device.query.filter_by(enabled=True).all()
    retval = [] 
    for d in devs: 
        retval.append(d.device_id) 
    return ({'devices': retval})   
        
# only disabled ids, from the database     
@app.route('/get/inactive/devices', methods=['GET'])      
def get_inactive_devices():    
    devs = Device.query.filter_by(enabled=False).all()
    retval = [] 
    for d in devs: 
        retval.append(d.device_id) 
    return ({'devices': retval})      
    
# return the devies whose room_name and relsen_name are blank (unconfigured devices)
@app.route('/get/new/devices', methods=['GET'])      
def get_new_devices():    
    # this code is adapted from get_relsen_tree ()
    relsens = Relsen.query.filter_by (relsen_name=None, room_name=None).all()
    retval = {} 
    for rs in relsens: 
        devid = rs.device_id
        rsid = rs.relsen_id        
        if (devid not in retval):
            retval[devid] = []
        retval[devid].append (rsid)    
    return (retval) 
    
                
#------------------------------------ Only Active Devices ------------------------------------
            
# all device json data as a list
@app.route('/dump/active/devices', methods =['GET']) 
def dump_active_devices(): 
    devs = Device.query.filter_by (enabled=True).all()
    retval = [] 
    for d in devs: 
        retval.append (d.toJSON())
    return ({'devices': retval}) 
        
# all device json data as a tree
@app.route('/dump/active/device/tree', methods =['GET']) 
def dump_active_device_tree(): 
    devs = Device.query.filter_by (enabled=True).all()
    retval = {} 
    for d in devs: 
        retval[d.device_id] = d.toJSON()
    return (retval) 
            
# technical specs            
@app.route('/dump/active/device/specs', methods =['GET']) 
def dump_active_device_specs(): 
    devs = Device.query.filter_by(enabled=True).all()
    retval = [] 
    for d in devs: 
        retval.append(d.get_device_specs())  
    return ({'devices': retval}) 
            
# specs as a tree            
@app.route('/dump/active/device/spec/tree', methods =['GET']) 
def dump_active_device_spec_tree(): 
    devs = Device.query.filter_by(enabled=True).all()
    retval = {} 
    for d in devs: 
        retval[d.device_id] = d.get_device_specs() 
    return (retval) 

#---------------------- filter a particular device --------------------------------------------

# dump a particular device along with its contained relsens
@app.route('/get/device/details', methods =['GET']) 
def get_device_details(): 
    devid = request.args.get('device_id')
    if (not devid):
        return ({'result' : False, 'error' : 'device_id is required'})
    dev = Device.query.filter_by (device_id=devid).first()
    if (not dev):
        return ({'result' : False, 'error' : 'invalid device_id'})
    return (dev.toJSON())    
    
# only config fields
@app.route('/get/device/config', methods =['GET']) 
def get_device_config ():
    devid = request.args.get('device_id')
    if (not devid):
        return ({'result' : False, 'error' : 'device_id is required'})
    dev = Device.query.filter_by (device_id=devid).first()
    if (not dev):
        return ({'result' : False, 'error' : 'invalid device_id'})
    return (dev.get_device_config()) 

# technical specs
@app.route('/get/device/specs', methods =['GET']) 
def get_device_specs ():
    devid = request.args.get('device_id')
    if (not devid):
        return ({'result' : False, 'error' : 'device_id is required'})
    dev = Device.query.filter_by (device_id=devid).first()
    if (not dev):
        return ({'result' : False, 'error' : 'invalid device_id'})
    return (dev.get_device_specs()) 

#---------------------------------------------------------------------------------------------------- 
# Relsens
#---------------------------------------------------------------------------------------------------- 

#------------------only the ids ---------------------------------------------------------------------

# all device_id and relsen_id, as a list      
@app.route('/get/relsens', methods =['GET']) 
@app.route('/get/relsen/list', methods =['GET']) 
def list_all_relsens(): 
    rels = Relsen.query.all()
    retval = [] 
    for rs in rels: 
        jrelson = {'device_id':rs.device_id, 'relson_id':rs.relsen_id}  
        retval.append (jrelson)          
    return ({'relsens': retval})  
                    
# all device_id and relsen_id, as a tree structure
@app.route('/get/relsen/tree', methods =['GET']) 
def get_relsen_tree (): 
    relsens = Relsen.query.all()
    retval = {} 
    for rs in relsens: 
        devid = rs.device_id
        rsid = rs.relsen_id        
        if (devid not in retval):
            retval[devid] = []
        retval[devid].append (rsid)    
    return (retval) 
                       
# all device_id and relsen_id, as a tree structure
@app.route('/get/friendly/relsen/tree', methods =['GET']) 
def get_friendly_relsen_tree (): 
    relsens = Relsen.query.all()
    retval = {} 
    for rs in relsens: 
        friend = rs.get_friendly_identifier()
        if rs.device_id not in retval:
            retval[rs.device_id] = []
        retval[rs.device_id].append (friend)    
    return (retval) 
                            
# active device_id and relsen_id, as a list
@app.route('/get/active/relsens', methods =['GET']) 
def get_active_relsens (): 
    ##relsens = Relsen.query.filter_by (controller.enabled=True).all() # TODO: use back_populates
    relsens = Relsen.query.all()
    retval = [] 
    for rs in relsens: 
        if (rs.controller.enabled):
            jrelson = {'device_id':rs.device_id, 'relson_id':rs.relsen_id}  
            retval.append (jrelson)          
    return ({'relsens': retval})   
                        
# active device_id and relsen_id, as a tree         
@app.route('/get/active/relsen/tree', methods =['GET']) 
def get_active_relsen_tree (): 
    relsens = Relsen.query.all()
    retval = {} 
    for rs in relsens: 
        if (rs.controller.enabled):
            devid = rs.device_id
            rsid = rs.relsen_id        
            if (devid not in retval):
                retval[devid] = []
            retval[devid].append (rsid)    
    return (retval)  

#-------------------------------------- complete relsen objects --------------------------------------------

# all - complete relsen objects as a list
@app.route('/dump/relsens', methods =['GET']) 
def dump_all_relsens(): 
    rels = Relsen.query.all()
    retval = [] 
    for rs in rels: 
        retval.append (rs.toJSON())          
    return ({'relsens': retval})     # all relsens are sibling nodes
    
# all - complete relsen objects as a tree
@app.route('/dump/relsen/tree', methods =['GET']) 
def dump_all_relsen_tree(): 
    rels = Relsen.query.all()
    retval = {} 
    for rs in rels: 
        devid = rs.device_id
        if (devid not in retval):
            retval[devid] = []
        retval[devid].append (rs.toJSON())
    return (retval)      
        
# active - complete relsen objects as a list
@app.route('/dump/active/relsens', methods =['GET']) 
def dump_active_relsens(): 
    rels = Relsen.query.all()
    retval = [] 
    for rs in rels: 
        if (rs.controller.enabled):
            retval.append (rs.toJSON())          
    return ({'relsens': retval})      
        
# active - complete relsen objects as a tree
@app.route('/dump/active/relsen/tree', methods =['GET']) 
def dump_active_relsen_tree(): 
    rels = Relsen.query.all()
    retval = {} 
    for rs in rels: 
        if (rs.controller.enabled):
            devid = rs.device_id
            if (devid not in retval):
                retval[devid] = []
            retval[devid].append (rs.toJSON())
    return (retval)  
    
#---------------------- filters --------------------------------------------------------------------------- 
    
#------------------------- find one particular relsesn by id ----------------------------------------------

# Get user friendly identifiers of a selected relsen
@app.route('/get/friendly/identifier', methods =['GET']) 
def get_friendly_identifier_route (): 
    devid = request.args.get('device_id')
    if (not devid):
        return ({'result' : False, 'error' : 'device_id is required'})
    relid = request.args.get('relsen_id')
    if (not relid):
        return ({'result' : False, 'error' : 'relsen_id is required'})
    rs = Relsen.query.filter_by(device_id=devid, relsen_id=relid).first()  
    if (not rs):
        return ({'result' : False, 'error' : 'invalid device_id or relsen_id'})    
    return (rs.get_friendly_identifier()) 
    

# JSON dump of the selected relsen
@app.route('/get/relsen/details', methods =['GET']) 
def get_relsen_details (): 
    devid = request.args.get('device_id')
    if (not devid):
        return ({'result' : False, 'error' : 'device_id is required'})
    relid = request.args.get('relsen_id')
    if (not relid):
        return ({'result' : False, 'error' : 'relsen_id is required'})
    rs = Relsen.query.filter_by(device_id=devid, relsen_id=relid).first()  
    if (not rs):
        return ({'result' : False, 'error' : 'invalid device_id or relsen_id'})    
    return (rs.toJSON()) 
            
#----------------------------------------------------------------------------------------------------------- 

# all relsens under a given device - only ids
@app.route('/get/attached/relsen/ids', methods=['GET']) 
def get_attached_relsen_ids():
    devid = request.args.get('device_id')
    if (not devid):
        return ({'result' : False, 'error' : 'device_id is required'})
    dev = Device.query.filter_by (device_id=devid).first()
    if (not dev):
        return ({'result' : False, 'error' : 'invalid device_id'})
    retval = {
        'device_id' : devid,
        'relsens' : dev.get_attached_relsen_ids()
    }
    return (retval)
    
# all relsens under a given device - complete dump
@app.route('/get/attached/relsens', methods=['GET'])  # full relsen objects under this device
def get_attached_relsens():
    devid = request.args.get('device_id')
    if (not devid):
        return ({'result' : False, 'error' : 'device_id is required'})
    dev = Device.query.filter_by (device_id=devid).first()
    if (not dev):
        return ({'result' : False, 'error' : 'invalid device_id'})
    retval = {
        'device_id' : devid,
        'relsens' : dev.get_attached_relsens()  # this is a list of serialized json objects
    }
    return (retval)
            
#------------------------------------------------------------------------------------------------------------
# search
#------------------------------------------------------------------------------------------------------------

'''---------- the following two calls do not make much sense! ---------------------------------=|
# devices by room  [devices are not attached to rooms, only relsens are]                        |
@app.route('/get/device/ids/in/room', methods=['GET'])                                          |
def get_device_ids_in_room():                                                                   |
    room = request.args.get('room_name')                                                        |
    if (not room):                                                                              |
        return ({'result' : False, 'error' : 'room_name is required'})                                            |
    relsens = Relsen.query.filter_by (room_name=room).all() # room_name is accessible only      |
                                                            # through one of its Relsens        |
    retval = set([])    # to avoid duplicates                                                   |
    for rs in relsens:                                                                          |
        retval.add (rs.device_id)                                                               |
    return ({'devices': list(retval)})  # set cannot be serialized                              |
                                                                                                |
@app.route('/get/devices/in/room', methods=['GET'])                                             |
def get_devices_in_room():                                                                      |
    room = request.args.get('room_name')                                                        |
    if (not room):                                                                              |
        return ({'result' : False, 'error' : 'room_name is required'})                                            |
    relsens = Relsen.query.filter_by (room_name=room).all()                                     |
    devices = set([])    # to avoid duplicates                                                  |
    for rs in relsens:                                                                          |
        devices.add (rs.controller)                                                             |
    dprint (devices)                                                                            |
    dprint (type(devices))                                                                      |
    retval = []                                                                                 |
    for d in devices:                                                                           |
        retval.append (d.toJSON())                                                              |
    return ({'devices': retval})                                                                |
------------------ revive them, if you need later --------------------------------------------'''   

# --- search by device_name + room_name  ---   
@app.route('/get/relsen/ids/by/name', methods=['GET'])      
def get_relsen_ids_by_name():    
    relname = request.args.get('relsen_name')
    if (not relname):
        return ({'result' : False, 'error' : 'relsen_name is required'})
    room = request.args.get('room_name')
    if (not room):
        return ({'result' : False, 'error' : 'room_name is required'})
    relsens = Relsen.query.filter_by (relsen_name=relname, room_name=room).all()
    return (build_relsen_ids_tree (relsens))
     
@app.route('/get/relsens/by/name', methods=['GET'])      
def get_relsens_by_name():    
    relname = request.args.get('relsen_name')
    if (not relname):
        return ({'result' : False, 'error' : 'relsen_name is required'})
    room = request.args.get('room_name')
    if (not room):
        return ({'result' : False, 'error' : 'room_name is required'})
    relsens = Relsen.query.filter_by (relsen_name=relname, room_name=room).all()
    return (build_relsen_details_tree (relsens))  # TODO: return only active relsens?
     
# --- by room name ---   
@app.route('/get/relsen/ids/in/room', methods=['GET'])      
def get_relsen_ids_in_room():    
    room = request.args.get('room_name')
    if (not room):
        return ({'result' : False, 'error' : 'room_name is required'})
    relsens = Relsen.query.filter_by (room_name=room).all()
    ###return (build_relsen_ids_tree (relsens))
    return (build_active_relsen_ids_tree (relsens))

    
@app.route('/get/relsens/in/room', methods=['GET'])     # TODO: return the complete relsen objects
def get_relsens_in_room():    
    room = request.args.get('room_name')
    if (not room):
        return ({'result' : False, 'error' : 'room_name is required'})
    relsens = Relsen.query.filter_by (room_name=room).all()
    ##return (build_relsen_details_tree (relsens))
    return (build_active_relsen_details_tree (relsens))
    
# -- by room type --
      
@app.route('/get/relsen/ids/of/room/type', methods=['GET'])      
def get_relsen_ids_of_room_type():    
    rtype = request.args.get('room_type')
    if (not rtype):
        return ({'result' : False, 'error' : 'room_type is required'})
    relsens = Relsen.query.filter_by (room_type=rtype).all()
    ###return (build_relsen_ids_tree (relsens))
    return (build_active_relsen_ids_tree (relsens)) 
                
@app.route('/get/relsens/of/room/type', methods=['GET'])      
def get_relsens_of_room_type():    
    rtype = request.args.get('room_type')
    if (not rtype):
        return ({'result' : False, 'error' : 'room_type is required'})
    relsens = Relsen.query.filter_by (room_type=rtype).all()
    ##return (build_relsen_details_tree (relsens))
    return (build_active_relsen_details_tree (relsens))
    
# --- by relsen type ---
                
@app.route('/get/relsen/ids/of/type', methods =['GET']) 
def get_relsen_ids_of_type():
    type = request.args.get('relsen_type')
    if (not type):
        return ({'result' : False, 'error' : 'relsen_type is required'})
    relsens = Relsen.query.filter_by (relsen_type=type).all()
    ###return (build_relsen_ids_tree (relsens))
    return (build_active_relsen_ids_tree (relsens))


@app.route('/get/relsens/of/type', methods =['GET']) 
def get_relsens_of_type():
    type = request.args.get('relsen_type')
    if (not type):
        return ({'result' : False, 'error' : 'relsen_type is required'})
    relsens = Relsen.query.filter_by (relsen_type=type).all()
    ##return (build_relsen_details_tree (relsens))
    return (build_active_relsen_details_tree (relsens))
    
# --- by group ---
    
@app.route('/get/relsen/ids/in/group', methods =['GET']) 
def get_relsen_ids_of_group():
    grp = request.args.get('group_name')
    if (not grp):
        return ({'result' : False, 'error' : 'group_name is required'})
    relsens = Relsen.query.filter_by (group_name=grp).all()
    ###return (build_relsen_ids_tree (relsens))
    return (build_active_relsen_ids_tree (relsens)) 


@app.route('/get/relsens/in/group', methods =['GET']) 
def get_relsens_of_group():
    grp = request.args.get('group_name')
    if (not grp):
        return ({'result' : False, 'error' : 'group_name is required'})
    relsens = Relsen.query.filter_by (group_name=grp).all()
    ##return (build_relsen_details_tree (relsens))
    return (build_active_relsen_details_tree (relsens))
    
#-------- onboarding ------------------------------
    
# onboard a new device
@app.route('/onboard/device', methods =['GET', 'POST']) 
def onboard_device_route():    
    if (request.method=='GET'):
        return ({'result' : False, 'error':'POST the new Device id and Relsen list as JSON'})
    if (not request.json):
        return ({'result' : False, 'error':'invalid Device data'})
    if onboard_device(request.json):
        return {'result' : True, 'msg' : 'device onboarded successfully'}
    return {'result' : False, 'error' : 'failed to onboard device'}

# onboard multiple devices    
@app.route('/bulk/onboard/devices', methods =['GET', 'POST']) 
def bulk_onboard_devices_route():    
    if (request.method=='GET'):
        return ({'result' : False, 'error':'POST the new Device id and Relsen list as JSON'})
    if (not request.json):
        return ({'result' : False, 'error':'invalid Device data'})
    if bulk_onboard_devices(request.json):
        return {'result' : True, 'msg' : 'all devices onboarded successfully'}
    return {'result' : False, 'error' : 'failed to onboard at least one device'}    
    

@app.route('/enable/device', methods =['GET'])
def enable_device_route():
    devid = request.args.get('device_id')
    if (not devid):
        return ({'result' : False, 'error' : 'device_id is required'})
    return enable_device (devid)
    

@app.route('/disable/device', methods =['GET'])
def disable_device_route():
    devid = request.args.get('device_id')
    if (not devid):
        return ({'result' : False, 'error' : 'device_id is required'})
    return disable_device (devid)
    
#-------------------------Status data [This is just a place holder] --------------------------------------------

@app.route('/get/last/db/status', methods =['GET'])  
def get_latest_db_status(): 
    dprint ('Status class not implemented')
    return ({'place_holder':'not implemented'})  # TODO: this is to get the last known status from the
                                                 # DB, for troubleshooting/ autopsy
    
    
@app.route('/get/all/db/status', methods =['GET'])  # This can return a large number of records!
def get_all_db_status():                            # Need to include device id and relsen id also
    return ({'place_holder':'not implemented'})
    # the following is for future development
    stat = Status.query.all()
    retval = [] 
    for s in stat: 
        jstatus = {'device_did' : s.device_id, 'time_stamp':s.time_stamp, 'online':s.online}
        jrel={"Relays":None}
        if (s.relay_status):
            jrel = json.loads(s.relay_status)
        jsen={"Sensors":None}
        if (s.sensor_values):
            jsen = {"Sensors":json.loads(s.sensor_values)}      
        jstatus.update (jrel)
        jstatus.update (jsen)
        retval.append (jstatus)      # TODO: map them one-on-one to the relsen_ids
    return ({'all_status': retval})

#-------------------------------------------------------------------------------------------------------
# TO AVOID CIRCULAR DEPENDENCY, DO THE IMPORTS AT THE END
#-------------------------------------------------------------------------------------------------------

#import intof.Bridge as b
from intof.Bridge import build_device_inventory, update_timer, build_active_device_inventory_route
from intof.HouseKeeper import dprint, simul_bulk_onboard
