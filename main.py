import sensor, image, time, pyb, math
sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.XGA)  # 80 * 60 / 160 * 120
sensor.skip_frames(time=2000)
sensor.set_auto_gain(False, 3.52183)
sensor.set_auto_whitebal(False, rgb_gain_db=(61.4454, 60.2071, 64.5892))
#sensor.set_auto_exposure(False, 10124)
sensor.set_vflip(True)
sensor.set_hmirror(True)
clock = time.clock()

#dist_in = pyb.Pin('P5', pyb.Pin.IN)
#dist_out = pyb.Pin('P6', pyb.Pin.OUT_PP)
in_1 = pyb.Pin('P2', pyb.Pin.OUT_PP)
in_2 = pyb.Pin('P3', pyb.Pin.OUT_PP)
in_3 = pyb.Pin('P4', pyb.Pin.OUT_PP)
in_4 = pyb.Pin('P5', pyb.Pin.OUT_PP)
laser = pyb.Pin('P6', pyb.Pin.OUT_PP)

stepper_motor = (in_1, in_2, in_3, in_4)

states = [(1, 0, 0, 1), (1, 1, 0, 0), (0, 1, 1, 0), (0, 0, 1, 1)]

servo = pyb.Servo(1)
#print('suc')
#laser = dist_out

trsh_blue = [(27, 61, -3, 18, -28, -11)]
trsh_oran = [(49, 59, 4, 23, 7, 21)]
rois = (303, 237, 416, 282)
n = 10
#sterr = 4 * math.asin(math.sin(math.radians(99) / 2) * math.sin(math.radians(89) / 2))
sterr = 4.07 / 0.87
H = 6.35
h = 1.5

def find_circ():
    img = sensor.snapshot()
    img.lens_corr(strength=1.8)
    return img.find_blobs(trsh_blue, invert=False, roi=rois, merge=True, threshold_cb=lambda x: x.roundness() >= .6)
    #return img.find_circles()

def find_ticks():
    img = sensor.snapshot()
    img.lens_corr(strength=1.8)
    return img.find_blobs(trsh_oran, invert=False, roi=rois, merge=True)

def draw_blobs():
    img = sensor.snapshot()
    img.lens_corr(strength=1.8)
    blobs_bl = img.find_blobs(trsh_blue, invert=False, roi=rois, merge=True, threshold_cb=lambda x: x.roundness() >= .7)
    blobs_or = img.find_blobs(trsh_oran, invert=False, roi=rois, merge=True)
    for blob in blobs_bl:
        img.draw_rectangle(blob.rect(), color=(0, 255, 0))
        img.draw_cross(blob.cx(), blob.cy(), color=(0,255,0))
        pyb.delay(10)

    for blob in blobs_or:
        img.draw_rectangle(blob.rect(), color=(255, 0, 0))
        img.draw_cross(blob.cx(), blob.cy(), color=(255, 0, 0))
        pyb.delay(10)

def dist():
    ...

def write_steps(n: int, direct: int):
    shift = 0
    for j in range(n):
        for i, pin in enumerate(stepper_motor):
            pin.value(states[shift % 4][i])
        shift += direct
        pyb.delay(15)

def px_to_cm(px, d):
    return math.sqrt(sterr * d  ** 2 / (1024 * 768)) * px

def cm_to_px(cm, d):
    return cm // (math.sqrt(sterr * d ** 2 / (1024 * 768)))
x_old = 1024 // 2
def move_to_point(x, y, d):
    global x_old
    """
    Move to point by cx, cy, distance to wall
    """
    # Move by y
    px_to_cm = math.sqrt((sterr*d**2)/(1024*768))
    tg_b = math.tan(math.radians(31))
    #print(px_to_cm)
    tg_O =  -1 * (H - (768 - y) * px_to_cm + d * tg_b - h) / d
    #print(tg_O)
    ang_O = math.degrees((math.atan(tg_O)))
    #print(ang_O)
    servo.angle(ang_O)

    # Move by x
    #print(cm_to_px(d, d))
    tetta = math.degrees(math.atan(abs(x - x_old) / cm_to_px(d, d)))
    tetta_steps = tetta // 0.18
    #print(tetta_steps, 1 if x - 1024 // 2 >= 0 else -1)
    write_steps(tetta_steps, 1 if x - x_old >= 0 else -1)
    x_old = x


def main():
    # Init
    pyb.delay(50)
    laser.high()
    servo.angle(0)
    distance = 143 # cm

    # Get tick info: cx, cy, area in pixels
    t_tick_x, t_tick_y, t_tick_area = 0, 0, 0
    for _ in range(n):
        t = find_ticks()
        t_tick_x += t[0].cx()
        t_tick_y += t[0].cy()
        t_tick_area += t[0].pixels()
        pyb.delay(5)
    tick_x, tick_y, tick_area = t_tick_x // n, t_tick_y // n, t_tick_area // n

    # Get blue-circles info
    t_circ_x, t_circ_y = [[] for _ in range(5)], [[] for _ in range(5)]
    for _ in range(n):
        t = find_circ()
        print(t)
        for ind, element in enumerate(t):
            t_circ_x[ind].append(element.cx())
            t_circ_y[ind].append(element.cy())
    blue_circ_x = list(sum(i) // len(i) for i in t_circ_x if len(i) != 0)
    blue_circ_y = list(sum(i) // len(i) for i in t_circ_y if len(i) != 0)
    blue_circ_c = list((blue_circ_x[i], blue_circ_y[i]) for i in range(len(find_circ())))

    print(blue_circ_c)
    move_to_point(blue_circ_c[0][0], blue_circ_c[0][1], distance)
    pyb.delay(100)
    move_to_point(blue_circ_c[1][0], blue_circ_c[1][1], distance)

if __name__ == '__main__':
    main()
