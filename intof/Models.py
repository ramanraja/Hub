from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
from intof import db
#from intof.HouseKeeper import dprint 

def model_test_method():
    print ('\n--- I am the model stub ! ---\n')
 
DPRINT_ENABLED = True
def dprint (*args):
    #app.logger.info (*args)
    if DPRINT_ENABLED:
        print (*args)
        
class User (db.Model): 
    id = db.Column(db.Integer, primary_key = True) 
    name = db.Column(db.String(32)) 
    email = db.Column(db.String(64), unique = True) 
    password = db.Column(db.String(128))  # a hash of the password is stored here

    def __repr__(self):
        return ('<{}_{}>'.format (self.name, self.id))
        
                
class Device (db.Model): 
    __tablename__ = 'device'  # this line is optional
    device_id = db.Column(db.String(16), primary_key=True, unique=True, nullable=False) 
    fallback_id = db.Column(db.String(32), unique=True, nullable=True)
    mac = db.Column(db.String(24), unique=True)
    ip = db.Column(db.String(24))
    hardware_type = db.Column(db.String(32), default='Generic') 
    num_relays = db.Column(db.Integer, default=1)
    num_sensors = db.Column(db.Integer, default=0) 
    enabled = db.Column(db.Boolean, default=True)
    RSSI = db.Column(db.Integer, default=0)  # maximum is 100%
    signal = db.Column(db.Integer, default=0) # dBm
    relsens = db.relationship ('Relsen', backref='controller')  # TODO: use back_populates
    stat = db.relationship ('Status', backref='controller')  # TODO: can you remove this list of stat objects?
    
    def get_attached_relsen_ids (self): # only relsen IDs, as a list
        relsen_ids = []
        for rs in self.relsens:
            relsen_ids.append(rs.relsen_id)
        return (relsen_ids)
        
    def get_attached_relsens (self):    # complete relsen objects, serialized as a json list
        rels = []
        for rs in self.relsens:
            rels.append(rs.toJSON())
        return (rels)
                
    def get_device_config (self):
        jdevice_config = {
            'device_id': self.device_id,
            'hardware_type': self.hardware_type, 
            'num_relays': self.num_relays,
            'num_sensors': self.num_sensors,
            'enabled': self.enabled,
        }
        return (jdevice_config)        

    def get_device_specs (self):  # config and technical specs
        jdev_specs = self.get_device_config()
        jdev_specs['relsen_count'] = len(self.relsens)  # must be = num_relays+num_sensors
        jdev_specs['mac'] = self.mac
        jdev_specs['ip'] = self.ip
        jdev_specs['RSSI'] = self.RSSI
        jdev_specs['signal'] = self.signal
        jdev_specs['fallback_id'] = self.fallback_id
        return (jdev_specs)  
        
    def toJSON (self):             # config and dump the entire set of relsens 
        jdevice = self.get_device_config()
        jdevice['relsens'] = []
        for rs in self.relsens:
            jdevice['relsens'].append (rs.toJSON())
        return (jdevice)    
                
    def __repr__(self):
        return ('<{}/{}>'.format (self.device_id, self.fallback_id))
#----------------------------------------------------------------------------------------------------

# NOTE: Combination of device_id + relsen_id must be unique        
class Relsen (db.Model): 
    __tablename__ = 'relsen'
    rowid = db.Column(db.Integer, primary_key=True) # built-in autoincrement field 
    device_id = db.Column(db.String(16), db.ForeignKey ('device.device_id'), nullable=False) 
    relsen_id = db.Column(db.String(32), nullable=False)         # 'POWER1', 'A0'
    relsen_name = db.Column(db.String(32))                       # 'Hall light'
    relsen_type = db.Column(db.String(32), default='Generic')    # 'bulb', 'Temperature', 'Light'
    room_name = db.Column(db.String(32))    # 'guest room'
    room_type = db.Column(db.String(32))    # 'bed room'
    group_name = db.Column(db.String(32))   # 'ground floor'
    schedule = db.Column(db.String(256))    # stringified JSON: "{'schedule' : [[10.30,11.30],[14.0,15.20]]}"
    repeat = db.Column(db.Boolean)   
    
    def get_friendly_identifier (self):
        jidentifier = {
            'device_id': self.device_id,
            'relsen_id': self.relsen_id,
            'relsen_name': self.relsen_name,
            'relsen_type': self.relsen_type,
            'room_name': self.room_name,
            'group_name': self.group_name,
        }
        return (jidentifier)
    
    def toJSON (self):
        jrelsen = {
            'device_id': self.device_id,
            'relsen_id': self.relsen_id,
            'relsen_name': self.relsen_name,
            'relsen_type': self.relsen_type,
            'room_name': self.room_name,
            'room_type': self.room_type,
            'group_name': self.group_name,
            'repeat': self.repeat
        }
        if self.schedule is not None:
            jrelsen.update(json.loads(self.schedule))  # merge the two json objects
        else:
            jrelsen['schedule'] = []        # create a 'schedule' node with an empty array
        return (jrelsen)
     
    def __repr__(self):
        return ('<{}.{}>'.format (self.device_id, self.relsen_id))
        
#----------------------------------------------------------------------------------------------------

class Status (db.Model):  # TODO: store realtime data and events in database
    __tablename__ = 'status'
    rowid = db.Column(db.Integer, primary_key=True) # built-in autoincrement field 
    device_id = db.Column(db.String(16), db.ForeignKey ('device.device_id'), nullable=False) 
    time_stamp = db.Column(db.DateTime(timezone=True), default=datetime.now)  # db.func.current_timestamp())  
    relay_status = db.Column(db.String(24))  # array within JSON
    sensor_values = db.Column(db.String(32)) # JSON
    event_type = db.Column(db.String(16))    # autonomous, command, response, event, health, info, error 
    online = db.Column(db.Boolean)   

    def __repr__(self):
        OL = 'Offline'
        if self.online: 
            OL='Online'
        return ('<{}.{}({})>'.format (self.rowid, self.device_id, OL))

#----------------------------------------------------------------------------------------------------
    
class RoomType (db.Model): 
    id = db.Column(db.Integer, primary_key = True) 
    type = db.Column(db.String(32)) 
    icon = db.Column(db.String(32)) 

    def __repr__(self):
        return ('<{}_{}>'.format (self.type, self.id))    
        
#----------------------------------------------------------------------------------------------------
    
class RelsenType (db.Model): 
    id = db.Column(db.Integer, primary_key = True) 
    type = db.Column(db.String(32)) 
    icon = db.Column(db.String(32)) 

    def __repr__(self):
        return ('<{}_{}>'.format (self.type, self.id))    
        
        