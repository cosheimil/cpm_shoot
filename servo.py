import time
from second_party.opio import do_write

pin = 1
width_S = 10**9 * 1

while(True):
    timer = time.time_ns()
    do_write(pin, '1')
    while(time.time_ns() - timer < width_S):
        pass
    do_write(pin, '0')