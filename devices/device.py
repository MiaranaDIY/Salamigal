import time

class Device:
#Global variable
    instant_count = 0
    def __init__(self):
        #Increment instant counter
        Device.instant_count += 1
        #load watt for power usage calculation and device property
        self.ontime = 0
        self.load_watt = 0
        self.name = 'Device'
        self.location = 'Location'
        self.group = 'Group'
        self.streaming = 0
        
    #Set device streaming state
    def set_streaming(self, s = 1):
        self.streaming = s
        return self.streaming
    
    #Set device name
    def set_name(self, nm = '-'):
        self.name = nm
        return nm
    
    #Set device location
    def set_location(self, lc = '-'):
        self.location = lc
        return lc
        
    #Set device group
    def set_group(self, gr = '-'):
        self.group = gr
        return gr
        
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
        if(self.state and int(self.ontime) > 0):
            return (int(time.time()) - int(self.ontime)) / 60 / 60
        else:
            return 0
        
    #Calculate power usage in Wh
    def get_usage(self):
        return self.get_ontime() * self.load_watt