import time
import threading
import subprocess

def gpio_write(gpio, value):
    subprocess.run(["opio", "write", "-d", str(gpio), str(value)])

def gpio_read(gpio, value):
    subprocess.run(["opio", "read", "-d", str(gpio), str(value)])


class PWM(threading.Thread):
    def __init__(self, period, duty_cycle):
       threading.Thread.__init__()
       self.stop = False
       self.gpio = -1
       self.period = period
       self.duty_cycle = duty_cycle
       

    def run(self):
        if self.gpio == -1:
            return -1

        while(not self.stop):
            start_ = time.time_ns()
            gpio_write(self.gpio, 1)
            duty_time = start_ + self.duty_cycle
            period_time = start_ + self.period
            while(time.time_ns() < duty_time):
                pass
            gpio_write(self.gpio, 0)
            while(time.time_ns() < period_time):
                pass


    def write(self, gpio, value):
        self.stop = True
        self.gpio = gpio
        self.stop = False
        self.run()


    def stop_pwm(self):
        self.stop = True
