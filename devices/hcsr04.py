#Setup logging
import logging
import logging.config
logging.config.fileConfig('logging.conf')
# create logger
logger = logging.getLogger('root')
import time
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)  # set board mode to Broadcom  
GPIO.setwarnings(False)
import devices.device as device

class HCSR04(device.Device):
    #Global variable
    instant_count = 0
    def __init__(self, GPIO_TRIGGER, GPIO_ECHO):
        #Increment instant counter
        HCSR04.instant_count += 1
        #HCSR04 state, 0 = off, 1 = on
        self.state = 1
        # Set pins as output and input
        self.GPIO_TRIGGER = GPIO_TRIGGER
        self.GPIO_ECHO = GPIO_ECHO
        GPIO.setup(self.GPIO_TRIGGER,GPIO.OUT)  # Trigger
        GPIO.setup(self.GPIO_ECHO,GPIO.IN)      # Echo
        
        # Set trigger to False (Low)
        GPIO.output(self.GPIO_TRIGGER, GPIO.LOW)

        # Allow module to settle
        time.sleep(0.5)
        
        #load watt for power usage calculation and HCSR04 property
        self.ontime = 0
        self.load_watt = 0
        self.name = 'Ultrasonic Pinger'
        self.location = 'Lokasi'
        self.group = 'HCSR04'
        self.streaming = 0
        self.instant_count = HCSR04.instant_count
        self.tank_height = 0
        self.uid = 'HCSR04-'+str(HCSR04.instant_count)
        self.record = []
        self.level = 0
        self.record_counter = 0
        self.record_sample = 100
    
    #Get range
    def get_range(self):
        # Send 10us pulse to trigger
        GPIO.output(self.GPIO_TRIGGER, True)
        time.sleep(0.00001)
        GPIO.output(self.GPIO_TRIGGER, False)
        timeout_counter = int(time.time())
        start = time.time()
        while GPIO.input(self.GPIO_ECHO)==0 and (int(time.time()) - timeout_counter) < 0.1:
          start = time.time()

        timeout_counter = int(time.time())
        stop = time.time()
        while GPIO.input(self.GPIO_ECHO)==1 and (int(time.time()) - timeout_counter) < 0.1:
          stop = time.time()

        # Calculate pulse length
        elapsed = stop-start

        # Distance pulse travelled in that time is time
        # multiplied by the speed of sound (cm/s)
        # The speed of sound is the distance traveled per unit time by a 
        # sound wave propagating through an elastic medium. In dry air at 20 °C (68 °F), 
        # the speed of sound is 343.2 metres per second (1,126 ft/s; 1,236 km/h; 768 mph; 667 kn), 
        # or a kilometre in 2.914 s or a mile in 4.689 s.
        distance = elapsed * 34320

        # That was the distance there and back so halve the value
        distance = distance / 2
        
        if(len(self.record) <= self.record_sample):
            self.record.append(distance)
            
        return distance
    
    #Get water level
    def get_level(self):
        if(len(self.record) <= self.record_sample):
            return self.level
        else:
            self.record[self.record_counter] = self.get_range()
            self.record_counter+=1
            if(self.record_counter == self.record_sample + 1):
                self.record_counter = 0
            mean = 0
            for r in self.record:
                mean += r
            mean = mean / self.record_sample
            level = self.tank_height - mean
            level_percent = level / self.tank_height * 100
            self.level = level_percent
            return level_percent
        