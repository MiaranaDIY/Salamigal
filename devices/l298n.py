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
import traceback

class L298N(device.Device):
    #Global variable
    instant_count = 0
    def __init__(self, PWM1, M1A, M1B, M2A, M2B, PWM2):
        #Increment instant counter
        L298N.instant_count += 1
        #L298n Motor PWM control
        self.PWM1 = PWM1
        self.PWM2 = PWM2
        self.speed = 0
        self.freq = 50
        #L298n Motor direction control
        self.M1A = M1A
        self.M1B = M1B
        self.M2A = M2A
        self.M2B = M2B
        #Setup pin mode
        try:
            GPIO.setup(self.PWM1, GPIO.OUT)
            GPIO.setup(self.M1A, GPIO.OUT)
            GPIO.setup(self.M1B, GPIO.OUT)
            GPIO.setup(self.M2A, GPIO.OUT)
            GPIO.setup(self.M2B, GPIO.OUT)
            GPIO.setup(self.PWM2, GPIO.OUT)
            self.pedal_left = GPIO.PWM(self.PWM1, self.freq) 
            self.pedal_right = GPIO.PWM(self.PWM2, self.freq) 
        except Exception as err:
            logging.error(traceback.format_exc())
        
        self.state = 1
        self.direction = 'Stopped'
        
        try:
            if(self.state == 1):
                self.started_time = int(time.time())
            else:
                self.started_time = 0
        except Exception as err:
            self.started_time = 0
            logging.error(traceback.format_exc())
        #load watt for power usage calculation and l298n property
        self.uid = 'L298N-'+str(L298N.instant_count)
        self.load_watt = 0
        self.name = 'L298N'
        self.location = 'Location'
        self.group = 'L298N'
        self.warming = 0
        
    
    def __del__(self):
        try:
            self.reset()
        except Exception as err:
            self.started_time = 0
            logging.error(traceback.format_exc())
                
    #Moving forward
    def move_forward(self):
        try:
            GPIO.output(self.M1A, GPIO.HIGH)
            GPIO.output(self.M1B, GPIO.LOW)  
            GPIO.output(self.M2A, GPIO.HIGH)
            GPIO.output(self.M2B, GPIO.LOW)
            self.direction = 'Forward'
        except Exception as err:
            logging.error(traceback.format_exc())

    #Moving backward
    def move_backward(self):
        try:
            GPIO.output(self.M1A, GPIO.LOW)
            GPIO.output(self.M1B, GPIO.HIGH)  
            GPIO.output(self.M2A, GPIO.LOW)
            GPIO.output(self.M2B, GPIO.HIGH)
            self.direction = 'Backward'
        except Exception as err:
            logging.error(traceback.format_exc())
    
    #Turn left
    def turn_left(self):
        try:
            GPIO.output(self.M1A, GPIO.LOW)
            GPIO.output(self.M1B, GPIO.HIGH)  
            GPIO.output(self.M2A, GPIO.HIGH)
            GPIO.output(self.M2B, GPIO.LOW)
            self.direction = 'Turn left'
        except Exception as err:
            logging.error(traceback.format_exc())
    
    #Turn right
    def turn_right(self):
        try:
            GPIO.output(self.M1A, GPIO.HIGH)
            GPIO.output(self.M1B, GPIO.LOW)  
            GPIO.output(self.M2A, GPIO.LOW)
            GPIO.output(self.M2B, GPIO.HIGH)
            self.direction = 'Turn right'
        except Exception as err:
            logging.error(traceback.format_exc())
    
    #Stop
    def stop(self):
        try:
            GPIO.output(self.M1A, GPIO.LOW)
            GPIO.output(self.M1B, GPIO.LOW)  
            GPIO.output(self.M2A, GPIO.LOW)
            GPIO.output(self.M2B, GPIO.LOW)
            self.direction = 'Stopped'
        except Exception as err:
            logging.error(traceback.format_exc())
        
    def set_speed(self, speed):
        try:
            self.speed = int(speed)
            self.pedal_left.stop()
            self.pedal_right.stop()
            self.pedal_left.start(speed)
            self.pedal_right.start(speed)
            #self.pedal_left.ChangeDutyCycle(speed)
            #self.pedal_right.ChangeDutyCycle(speed)
            #time.sleep(0.2)
        except Exception as err:
            logging.error(traceback.format_exc())  
    
    def warm_up(self, send_dev_list, mid, sid, uid):
        #GPIO.setup(25, GPIO.OUT)
        #p = GPIO.PWM(25, 50)  # channel=12 frequency=50Hz
        self.warming = 1
        self.pedal_left.start(0)
        self.pedal_right.start(0)
        try:
            self.move_forward()
            started = int(time.time())
            while int(time.time()) - started < 60:
                for dc in range(0, 101, 1):
                    self.speed = dc
                    self.pedal_left.ChangeDutyCycle(dc)
                    self.pedal_right.ChangeDutyCycle(dc)
                    send_dev_list(mid, sid, uid)
                    time.sleep(0.1)
                for dc in range(100, -1, -1):
                    self.speed = dc
                    self.pedal_left.ChangeDutyCycle(dc)
                    self.pedal_right.ChangeDutyCycle(dc)
                    send_dev_list(mid, sid, uid)
                    time.sleep(0.1)
        except KeyboardInterrupt:
            pass
        self.reset()
        self.warming = 0
        return True
    
    def reset(self):
        try:
            self.stop()
            self.pedal_left.stop()
            self.pedal_right.stop()
        except Exception as err:
            logging.error(traceback.format_exc())              