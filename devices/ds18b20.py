#Setup logging
import logging
import logging.config
logging.config.fileConfig('logging.conf')
# create logger
logger = logging.getLogger('root')
import time
import devices.device as device
from w1thermsensor import W1ThermSensor as TS

class DS18B20(device.Device):
    #Global variable
    instant_count = 0
    def __init__(self, UID):
        #Increment instant counter
        DS18B20.instant_count += 1
        #DS18B20 state, 0 = off, 1 = on
        self.state = 1
        #load watt for power usage calculation and DS18B20 property
        self.uid = UID
        self.ontime = 0
        self.load_watt = 0
        self.name = 'Sensor Suhu'
        self.location = 'Lokasi'
        self.group = 'DS18B20'
        self.streaming = 0
        self.instant_count = DS18B20.instant_count
    
    
    #Get temperature
    def get_temp(self):
        dev = TS(TS.THERM_SENSOR_DS18B20, self.uid)
        return dev.get_temperature()
        