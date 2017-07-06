import uarm_async
import re
import time

class UArm:

    def __init__(self):
        self.uaa = uarm_async.UArmAsync()

    def connect(self,port=None):
        self.uaa.connect(port)

    def close(self):
        self.uaa.close()

    def wait_ready(self):
        return self.uaa.wait_ready()

    def set_position(self,x,y,z,f):
        cmd = 'G0 X{} Y{} Z{} F{}'.format(x,y,z,f)
        uaacf = self.uaa.send_cmd(cmd)
        return _UArmFuture(uaacf,lambda line:line=='ok')

    def get_position(self):
        cmd = 'P2220'
        uaacf = self.uaa.send_cmd(cmd)
        return _UArmFuture(uaacf,get_position_func)

    def attach_servo(self, servo_id):
        cmd = 'M2201 N{}'.format(servo_id)
        uaacf = self.uaa.send_cmd(cmd)
        return _UArmFuture(uaacf,lambda line:line=='ok')

    def detach_servo(self, servo_id):
        cmd = 'M2202 N{}'.format(servo_id)
        uaacf = self.uaa.send_cmd(cmd)
        return _UArmFuture(uaacf,lambda line:line=='ok')

    def set_user_mode(self,mode_id):
        cmd = 'M2400 S{}'.format(mode_id)
        uaacf = self.uaa.send_cmd(cmd)
        return _UArmFuture(uaacf,lambda line:line=='ok')

    def get_moving(self):
        cmd = 'M2200'
        uaacf = self.uaa.send_cmd(cmd)
        return _UArmFuture(uaacf,get_moving_func)

    def wait_stop(self):
        while(self.get_moving().wait()):
            time.sleep(0.01)

def get_position_func(line):
    m = re.fullmatch('ok X(\\S+) Y(\\S+) Z(\\S+)',line)
    if m:
        return float(m.group(1)),float(m.group(2)),float(m.group(3))
    return None

def get_moving_func(line):
    m = re.fullmatch('ok V(\\S+)',line)
    if m:
        return m.group(1) == '1'
    return None

class _UArmFuture:

    def __init__(self, uaacf, func):
        self.uaacf = uaacf
        self.func = func
    
    def wait(self):
        ret = self.uaacf.wait()
        return self.func(ret)

    def is_busy(self):
        return self.uaacf.is_busy()
