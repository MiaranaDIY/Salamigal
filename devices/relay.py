#Setup logging
import logging
import logging.config
logging.config.fileConfig('logging.conf')
# create logger
logger = logging.getLogger('root')
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)  # set board mode to Broadcom  
GPIO.setwarnings(False)
import devices.device as device
import time

class Relay(device.Device):
    #Global variable
    instant_count = 0
    def __init__(self, PIN):
        #Increment instant counter
        Relay.instant_count += 1
        #Relay state, 0 = off, 1 = on
        self.pin = PIN
        #Setup relay pin to output mode
        GPIO.setup(self.pin, GPIO.OUT)
        self.state = GPIO.input(self.pin)
        try:
            if(self.state == 1):
                self.started_time = int(time.time())
            else:
                self.started_time = 0
        except Exception as err:
            self.started_time = 0
            pass
        #load watt for power usage calculation and relay property
        self.uid = 'R'+str(Relay.instant_count)
        self.load_watt = 0
        self.name = 'Relay'
        self.location = 'Location'
        self.group = 'Relay'
        self.streaming = 0
          
    
    #Turn relay on or off
    def turn(self, s):
        try:
            s = int(s)
            if(s == 0 or s == 1):
                GPIO.output(self.pin, s)
                self.state = GPIO.input(self.pin)
                #set ontime for statistic
                if(s == 1):
                    self.started_time = time.time()
                else:
                    self.started_time = 0
                return s
            return None
        except Exception as err:
            logging.error("%s", traceback.format_exc())
            return None