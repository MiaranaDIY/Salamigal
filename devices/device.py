import time

class Device:
#Global variable
    instant_count = 0
    def __init__(self):
        #Increment instant counter
        Device.instant_count += 1
        #load watt for power usage calculation and device property
        self.load_watt = 0
        self.name = 'Device'
        self.location = 'Location'
        self.group = 'Group'
        self.streaming = 0
        self.state = 1
        self.started_time = time.time()
        
    #Set device load watt
    def set_watt(self, lw = 0):
        try:
            self.load_watt = int(lw)
            return lw
        except Exception as err:
            return None
        pass   
    
    #Get device ON time to calculate power usage (Hours)
    def get_ontime(self):
        if(self.state):
            return (int(time.time()) - int(self.started_time)) / 60 / 60
        else:
            return 0
        
    #Calculate power usage in Wh
    def get_usage(self):
        try:
            return self.get_ontime() * int(self.load_watt)
        except Exception as err:
            return None
        pass  