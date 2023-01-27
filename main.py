import sensor, image, time, pyb, math

sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.XGA)
sensor.skip_frames(time=2000)
sensor.set_auto_gain(False, 3.52183)
sensor.set_auto_whitebal(False, rgb_gain_db=(61.4454, 60.2071, 64.5892))
sensor.set_vflip(True)
sensor.set_hmirror(True)
clock = time.clock()

in_1 = pyb.Pin('P6', pyb.Pin.OUT_PP)
in_2 = pyb.Pin('P5', pyb.Pin.OUT_PP)
in_3 = pyb.Pin('P4', pyb.Pin.OUT_PP)
in_4 = pyb.Pin('P3', pyb.Pin.OUT_PP)
laser = pyb.Pin('P2', pyb.Pin.OUT_PP)
servo = pyb.Servo(1)
servo2 = pyb.Servo(2)
button = pyb.Pin('P9', pyb.Pin.IN)
blue_led = pyb.LED(3)

stepper_motor = (in_1, in_2, in_3, in_4)

states = [(1, 0, 0, 1), (1, 1, 0, 0), (0, 1, 1, 0), (0, 0, 1, 1)]

trsh_blue = [(20, 66, 9, 32, -52, -40)]
trsh_oran = [(57, 95, 27, 49, -30, 6)]
rois = (215, 356, 424, 246)
n = 10
#sterr = 4 * math.asin(math.sin(math.radians(99) / 2) * math.sin(math.radians(89) / 2))
sterr = 4.07 * 0.8
H = 6.35
h = 1.5
x_old = 1024 // 2

def sort_circles(circ, tick):
    x_center, y_center = tick[0], tick[1]
    swapped = True
    while swapped:
        swapped = False
        for i in range(len(circ) - 1):
            x_c1, y_c1 = circ[i][0], circ[i][1]
            x_c2, y_c2 = circ[i + 1][0], circ[i + 1][1]
            dist1 = math.sqrt((x_c1 - x_center) ** 2 + (y_c1 - y_center) ** 2)
            dist2 = math.sqrt((x_c2 - x_center) ** 2 + (y_c2 - y_center) ** 2)
            print(dist1, dist2)
            if abs(dist1 - dist2) <= 10:
                if x_c1 > x_c2:
                    circ[i], circ[i + 1] = circ[i + 1], circ[i]


def find_circ():
    """
    Func to find blue circles in rois with roundness more than .6 and merge all
    """
    img = sensor.snapshot()
    img.lens_corr(strength=1.8)
    return img.find_blobs(trsh_blue, invert=False, roi=rois, merge=True, threshold_cb=lambda x: x.roundness() >= .4)
    #return img.find_circles()

def find_ticks():
    """
    Func to find red ticks in rois
    """
    img = sensor.snapshot()
    img.lens_corr(strength=1.8)
    return img.find_blobs(trsh_oran, invert=False, roi=rois, merge=True)

def draw_blobs():
    """
    Debug func to draw blobs including circles and tick(s)
    """
    img = sensor.snapshot()
    img.lens_corr(strength=1.8)
    blobs_bl = img.find_blobs(trsh_blue, invert=False, roi=rois, merge=True, threshold_cb=lambda x: x.roundness() >= .6)
    blobs_or = img.find_blobs(trsh_oran, invert=False, roi=rois, merge=True)
    for blob in blobs_bl:
        img.draw_rectangle(blob.rect(), color=(0, 255, 0))
        img.draw_cross(blob.cx(), blob.cy(), color=(0,255,0))
        pyb.delay(10)

    for blob in blobs_or:
        img.draw_rectangle(blob.rect(), color=(255, 0, 0))
        img.draw_cross(blob.cx(), blob.cy(), color=(255, 0, 0))
        pyb.delay(10)

def write_steps(n: int, direct: int):
    """
    Write steps to motor and apply direction
    """
    shift = 0
    for j in range(n):
        for i, pin in enumerate(stepper_motor):
            pin.value(states[shift % 4][i])
        shift += direct
        pyb.delay(30)

def px_to_cm(px, d):
    """
    Func to convert px to cm using sterr
    """
    return math.sqrt(sterr * d  ** 2 / (1024 * 768)) * px

def cm_to_px(cm, d):
    """
    Func to convert cm to px using sterr
    """
    return cm // (math.sqrt(sterr * d ** 2 / (1024 * 768)))


def move_to_point(x, y, y_0, d):
    """
    Move to point by cx, cy, distance to wall
    """
    global x_old
    # Move by y
    #px_to_cm = math.sqrt((sterr*d**2)/(1024*768))
    #tg_b = math.tan(math.radians(31))
    #tg_O =  -1 * (H - (768 - y) * px_to_cm + d * tg_b - h) / d
    print(y)
    print(px_to_cm(y_0 - y, d))
    ang = math.degrees(math.asin(px_to_cm(y_0 - y, d) * math.sin(math.radians(70)) / (d + 1.2)))
    servo.angle(ang)
    print(ang)

    # Move by x
    print(px_to_cm(x - x_old, d))
    tetta = math.degrees(math.atan(abs(x - x_old) / cm_to_px(d, d)))
    servo2.angle(-1 * tetta if x >= x_old else tetta)
    x_old = x


def main():
    # Init
    pyb.delay(50)
    #laser.high()
    servo.angle(0)

    # Get tick info: cx, cy, area in pixels AND distance to wall
    t_tick_x, t_tick_y, t_tick_area = 0, 0, 0
    for _ in range(n):
        t = find_ticks()
        t_tick_x += t[0].cx()
        t_tick_y += t[0].cy()
        t_tick_area += t[0].pixels()
        pyb.delay(5)
    tick_x, tick_y, tick_area = t_tick_x // n, t_tick_y // n, t_tick_area // n
    tick = (tick_x, tick_y)
    #distance = 132 * 862 / tick_area

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
    blue_circs = list((blue_circ_x[i], blue_circ_y[i]) for i in range(len(find_circ())))
    button_value = button.value()

    # Now sort circles in true plan
    #print(blue_circs)
    blue_circs = sorted(blue_circs, key=lambda x: math.sqrt((x[0] - tick[0]) ** 2 + (x[1] - tick[1]) ** 2))
    sort_circles(blue_circs, tick)

    px_area = 88 / tick_area

    full_area = 1024*768*px_area

    distance = math.sqrt(full_area / sterr)

    y_0 = 559
    print(distance, full_area)
    #print(blue_circs)
    print("ready")
    #y_old = y_0
    #Solve the problem
    laser.high()
    for circl in blue_circs:
        print(circl)
        blue_led.off()
        while button.value() == 0:
            pyb.delay(200)
        move_to_point(circl[0], circl[1], y_0,distance)
        pyb.delay(200)
        blue_led.on()
        y_old = circl[1]
    blue_led.off()
    #write_steps(abs(x_old), -1 if x_old > 0 else 1)


def exp():
    servo2.angle(-30)
    laser.high()
    while True:
        img = sensor.snapshot()
        img.lens_corr(strength=1.8)
        pyb.delay(100)

if __name__ == '__main__':
    #exp()
    main()
