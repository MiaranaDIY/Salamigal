# -*- coding: utf-8 -*-
#Setup logging
import logging
import logging.config
logging.config.fileConfig('logging.conf')
# create logger
logger = logging.getLogger('root')
import multiprocessing
import threading
import time
import traceback
import subprocess as sp
import json
from devices.relay import Relay
from devices.ds18b20 import DS18B20

#Manually create relay 1
relay_1 = Relay(17)
relay_1.set_name("Lampu Utama")
relay_1.set_location("Kamar Tamu")
relay_1.set_group("Relay")
relay_1.set_watt(45)

#Manually create relay 2
relay_2 = Relay(18)
relay_2.set_name("AC Samsung 1PK")
relay_2.set_location("Kamar")
relay_2.set_group("Relay")
relay_2.set_watt(500)

#Manually create ds18b20 1
ds18b20_1 = DS18B20('000005504c8b')
ds18b20_1.set_name("Sensor Suhu Kamar")
ds18b20_1.set_location("Kamar")
ds18b20_1.set_group("DS18B20")
ds18b20_1.set_watt(0.1)


class SalamigalNetworking(multiprocessing.Process):

    def __init__(self, taskQ, resultQ):
        super(SalamigalNetworking, self).__init__()
        multiprocessing.Process.__init__(self)
        self.resultQ = resultQ
        self.taskQ = taskQ
        self.stream_thread = []
    
    #Manually create device list to be send to client
    def send_dev_list(self, mid, sid, uid="*"):
        global relay_1
        global relay_2
        try:     
            dev = [
                {
                    'uid': {'label': 'UID', 'value': relay_1.uid},
                    'name': {'label': 'Device Name', 'value':  relay_1.name},
                    'location': {'label': 'Location', 'value': relay_1.location},
                    'group': {'label': 'Group/Type', 'value':relay_1.group},
                    'watt': {'label': 'Load (Watt)', 'value': relay_1.load_watt},
                    'ontime': {'label': 'ON time (Hours)', 'value': round(relay_1.get_ontime(),2)},
                    'state': {'label': 'Load State', 'value': relay_1.state},
                    'stream': {'label': 'Streaming', 'value': relay_1.streaming},
                    'usage': {'label': 'Usage (Wh)', 'value': round(relay_1.get_usage(),2)}
                },
                {
                    'uid': {'label': 'UID', 'value': relay_2.uid},
                    'name': {'label': 'Device Name', 'value':  relay_2.name},
                    'location': {'label': 'Location', 'value': relay_2.location},
                    'group': {'label': 'Group/Type', 'value':relay_2.group},
                    'watt': {'label': 'Load (Watt)', 'value': relay_2.load_watt},
                    'ontime': {'label': 'ON time (Hours)', 'value':  round(relay_1.get_ontime(),2)},
                    'state': {'label': 'Load State', 'value': relay_2.state},
                    'stream': {'label': 'Streaming', 'value': relay_2.streaming},
                    'usage': {'label': 'Usage (Wh)', 'value': round(relay_2.get_usage(),2)}
                },
                {
                    'uid': {'label': 'UID', 'value': ds18b20_1.uid},
                    'name': {'label': 'Device Name', 'value':  ds18b20_1.name},
                    'location': {'label': 'Location', 'value': ds18b20_1.location},
                    'group': {'label': 'Group/Type', 'value':ds18b20_1.group},
                    'stream': {'label': 'Streaming', 'value': ds18b20_1.streaming},
                    'temp': {'label': 'Temperature (C)', 'value': ds18b20_1.get_temp()}
                }
            ]
            if(uid == "*"):
                dev = {
                    'dev': dev
                }
                self.send_message(dev,mid,to=sid)
                return dev
            else:
                for d in dev:
                    if(d['uid']['value'] == uid):
                        dev = {
                            'dev': [d]
                        }
                        self.send_message(dev,mid,to=sid)
                        return dev
                return None
        except Exception as err:
            logging.error("%s", traceback.format_exc())
            return None
            
    #Manually create all device list and return the value or queried value
    def get_dev_list(self, uid="*"):
        global relay_1
        global relay_2
        try:     
            dev = [
                {
                    'uid': relay_1.uid,
                    'obj': relay_1
                },
                {
                    'uid': relay_2.uid,
                    'obj': relay_2
                },
                {
                    'uid': ds18b20_1.uid,
                    'obj': ds18b20_1
                }
            ]
            if(uid == "*"):
                return dev
            else:
                for d in dev:
                    if(d['uid'] == uid):
                        return d['obj']
                return None
        except Exception as err:
            logging.error("%s", traceback.format_exc())
            return None

    #Function for changing device property
    def set_dev(self, uid, param, val, sid, mid):
        dev = self.get_dev_list(uid)
        #Special relay
        if(dev.group == 'Relay'):
            if(param == 'state'):
                dev.turn(val)
                #Update device change to client
                self.send_dev_list(mid, sid, uid)
            elif(param == 'stream'):
                if(val == 1):
                    self.stream_start(uid, mid, sid)
                else:
                    self.stream_stop(uid, mid, sid)
        #Special DS18B20
        if(dev.group == 'DS18B20'):
            if(param == 'stream'):
                if(val == 1):
                    self.stream_start(uid, mid, sid)
                else:
                    self.stream_stop(uid, mid, sid)
    
    #Function to initialize and start device stream threading
    def stream_start(self, uid, mid, sid='*'):
        dev = self.get_dev_list(uid)
        if(dev.streaming):
            dev.set_streaming(0)
            self.send_dev_list(mid, sid, uid)
            return None
        dev.set_streaming(1)
        t_stream_dev = threading.Thread(name='Device Streamer', target=self.dev_streamer, args=[uid, mid, sid])
        t_stream_dev.daemon = True
        t_stream_dev.start()
        
    def stream_stop(self, uid, mid, sid='*'):
        dev = self.get_dev_list(uid)
        dev.set_streaming(0)
        self.send_dev_list(mid, sid, uid)
    
    #Function to stream all or specific device data & property
    def dev_streamer(self, uid, mid, sid):
        dev = self.get_dev_list(uid)
        logging.info('Streaming device {} to {} started'.format(dev.name, mid))

        while dev.streaming == 1:
            dev = self.get_dev_list(uid)
            self.send_dev_list(mid, sid, uid)
            

            time.sleep(1)
        logging.info('Streaming device {} to {} stopped'.format(dev.name, mid))
    
    #Send message to client   
    def send_message(self, data, mid, to='*', stat='complete', is_binary=False):
        rpl = {
            'is_binary': is_binary,
            'data' : {
                '$id': mid,
                '$type': stat,
                'data': data
            },
            'to': '*'
        }
        self.resultQ.put(rpl)
        return(rpl)
    
    
    def run(self): 
        logging.info("** {} process started".format(self.__class__.__name__))
        while True:
            try:
                if not self.taskQ.empty():
                    queue = self.taskQ.get()
                    task = queue['task']
                    cmd = queue['cmd']
                    arg = queue['arg']
                    sid = queue['sid']
                    mid = queue['mid']
                    
                    #Command parsing
                    if(cmd == "req_dev"):
                        self.send_dev_list(mid, sid, arg)
                    elif(cmd == "set_dev"):
                        self.set_dev(arg['uid'], arg['param'], arg['val'], sid, mid)
                    
                    
                time.sleep(0.05)
            except Exception as err:
                logging.error("%s", traceback.format_exc())
                return None
        logging.info("** {} process stopped".format(self.__class__.__name__))
