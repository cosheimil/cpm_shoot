import sensor
import image
import time
import pyb
import math

sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.XGA)
sensor.skip_frames(time=2000)
# sensor.set_auto_gain(False, 3.52183)
#sensor.set_auto_whitebal(False, rgb_gain_db=(61.4454, 6r0.2071, 64.5892))
sensor.set_vflip(True)
sensor.set_hmirror(True)
clock = time.clock()

dist_out = pyb.Pin('P4', pyb.Pin.OUT_PP)
dist_in = pyb.Pin('P3', pyb.Pin.IN, pyb.Pin.PULL_UP)
laser = pyb.Pin('P2', pyb.Pin.OUT_PP)
servo = pyb.Servo(1)
servo2 = pyb.Servo(2)
button = pyb.Pin('P9', pyb.Pin.IN)
blue_led = pyb.LED(3)
green_led = pyb.LED(2)

trsh_blue = [(14, 61, 11, 31, -78, -24)]
trsh_oran = [(41, 60, 23, 54, -28, -10)]
rois = (0, 0, 1024, 768)

cam_angle_y = 80
cam_angle_z = 0.0
n = 10
X = 1024
Y = 768
VFOV     = 81.9
HFOV = 99


class vector_3d:
    x = 0
    y = 0
    z = 0

    def __init__(self, coords: tuple[float]):
        (self.x, self.y, self.z) = coords

    def __add__(self, a):
        return vector_3d((self.x + a.x, self.y + a.y, self.z + a.z))

    def __sub__(self, a):
        return vector_3d((self.x - a.x, self.y - a.y, self.z - a.z))

    def rotate(self, axis, angle):
        angle = math.radians(angle)
        _cos = math.cos(angle)
        _sin = math.sin(angle)
        if axis == 0:
            self.x = self.x
            self.y = self.y * _cos - self.z * _sin
            self.z = self.y * _sin + self.z * _cos
        elif axis == 1:
            self.x = self.x * _cos + self.z * _sin
            self.y = self.y
            self.z = -self.x * _sin + self.z * _cos
        elif axis == 2:
            self.x = self.x * _cos - self.y * _sin
            self.y = self.x * _sin + self.y * _sin
            self.z = self.z
        else:
            print(f"Wrong axis:{axis}!")

    def get_coords(self):
        return (self.x, self.y, self.z)


servo_0_pos = vector_3d((-6.65, 0.02, 1.14))
servo_1_pos = vector_3d((-0.43, -1.4, 1.38))


def get_laser_pos(point: vector_3d, h_laser=1.42):
    x_1 = point.x
    z_1 = point.z

    D = 4*(x_1**2 * h_laser**4 - (x_1**2 + z_1**2)
           * (h_laser**4 - z_1**2 * h_laser**2))
    sq_D = math.sqrt(D)

    if z_1 > 0:
        x_2 = (x_1*h_laser**2 - sq_D) / (2*(x_1**2 + z_1**2))
        z_2 = math.sqrt(h_laser**2 - x_2**2)
    else:
        x_2 = (x_1*h_laser**2 + sq_D) / (2*(x_1**2 + z_1**2))
        z_2 = math.sqrt(h_laser**2 - x_2**2)

    return vector_3d((x_2, point.y, z_2))


def sort_circles(circ, tick):
    """
    Sort circles in true sign after sorting by distance
    """
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
    return img.find_blobs(trsh_blue, invert=False, merge=True, threshold_cb=lambda x: x.roundness() >= .8 and 80 <= x.pixels() <= 900)
    # return img.find_circles()


def find_ticks():
    """
    Func to find red ticks in rois
    """
    img = sensor.snapshot()
    img.lens_corr(strength=1.8)
    return img.find_blobs(trsh_oran, invert=False, roi=rois, merge=True, threshold_cb=lambda x: x.pixels() >= 500 and x.roundness() >= .8)


def draw_blobs():
    """
    Debug func to draw blobs including circles and tick(s)
    """
    img = sensor.snapshot()
    img.lens_corr(strength=1.8)
    blobs_bl = img.find_blobs(trsh_blue, invert=False, roi=rois,
                              merge=True, threshold_cb=lambda x: x.roundness() >= .6)
    blobs_or = img.find_blobs(trsh_oran, invert=False, roi=rois, merge=True)
    for blob in blobs_bl:
        img.draw_rectangle(blob.rect(), color=(0, 255, 0))
        img.draw_cross(blob.cx(), blob.cy(), color=(0, 255, 0))
        pyb.delay(10)

    for blob in blobs_or:
        img.draw_rectangle(blob.rect(), color=(255, 0, 0))
        img.draw_cross(blob.cx(), blob.cy(), color=(255, 0, 0))
        pyb.delay(10)


def get_dist_to_point(angle_to_point, L):
    return L / math.cos(math.radians(180 - (angle_to_point + cam_angle_y)))


def dist():
    """
    dist_out = pyb.Pin('P3', pyb.Pin.OUT_PP)
    dist_in = pyb.Pin('P4', pyb.Pin.IN)
    """
    # Сначала генерируем короткий импульс длительностью 2-5 микросекунд.
    dist_out.value(0)
    time.sleep_us(2)
    dist_out.value(1)
    # Выставив высокий уровень сигнала, ждем около 10 микросекунд. В этот момент датчик будет посылать сигналы с частотой 40 КГц.
    time.sleep_us(10)
    dist_out.value(0)
    while dist_in.value() != 1:
        ...
    start = time.ticks_us()
    while dist_in.value() != 0:
        ...
    t = time.ticks_us() - start
    cm = t / (2 * 29.1)
    pyb.delay(50)
    return cm


val_list = [0] * n
ind = 0


def run_middle_arifm(value):
    global val_list
    global ind
    val_list[ind] = value
    if ind + 1 >= n:
        ind = 0
    av = sum(val_list)
    ind += 1
    return av / n

def get_point(px_coords, L):
    (px_x, px_y) = px_coords
    px_x = -px_x + X/2
    px_y = -px_y + Y/2

    theta = 0.5*math.pi - \
        math.atan((2.0*float(px_y)/Y) *
                  math.tan(math.radians(0.5 * VFOV)))

    phi = math.atan((2.0*float(px_x)/X) *
                    math.tan(math.radians(0.5 * HFOV)))

    r = get_dist_to_point(math.degrees(theta), L) / math.cos(phi)

    # Got r, phi, theta; how will get x, y, z
    x = r * math.sin(theta) * math.cos(phi)
    y = r * math.sin(theta) * math.sin(phi)
    z = r * math.cos(theta)

    point = vector_3d((x, y, z))

    point.rotate(axis=1, angle=-(90 - cam_angle_y))

    return point.get_coords()

def get_point_angles(px_coords, L):
    (px_x, px_y) = px_coords
    px_x = -px_x + X/2
    px_y = -px_y + Y/2

    theta = 0.5*math.pi - \
        math.atan((2.0*float(px_y)/Y) *
                  math.tan(math.radians(0.5 * VFOV)))

    phi = math.atan((2.0*float(px_x)/X) *
                    math.tan(math.radians(0.5 * HFOV)))

    r = get_dist_to_point(math.degrees(theta), L) / math.cos(phi)

    # Got r, phi, theta; how will get x, y, z
    x = r * math.sin(theta) * math.cos(phi)
    y = r * math.sin(theta) * math.sin(phi)
    z = r * math.cos(theta)

    point = vector_3d((x, y, z))

    point.rotate(axis=1, angle=-(90 - cam_angle_y))

    point = point - vector_3d(servo_0_pos.get_coords())
    #! artcg(y / x) = phi
    phi = math.degrees(math.atan(y / x))

    _servo_1_pos = vector_3d(servo_1_pos.get_coords())

    point = point - _servo_1_pos

    _laser_pos = get_laser_pos(point)

    point = point - _laser_pos

    theta = math.degrees(math.atan(math.sqrt(point.x**2 + point.y**2)/point.z))

    if theta < 0:
        theta = -90 - theta
    else:
        theta = 90 - theta

    if phi != 0.0:
        phi = -phi

# phi is an angle for servo_0, theta is for servo_1
    return -1 * phi, theta


def main():
    # Init
    pyb.delay(10)

    # Get dist to table
    for _ in range(n):
        L = run_middle_arifm(dist())
    print(L)

    # Get tick info: cx, cy, area in pixels AND distance to wall
    t_tick_x, t_tick_y, t_tick_area = 0, 0, 0
    for _ in range(n):
        t = find_ticks()
        if len(t) == 1:
            t_tick_x += t[0].cx()
            t_tick_y += t[0].cy()
            t_tick_area += t[0].pixels()
            pyb.delay(5)
    tick_x, tick_y, tick_area = t_tick_x // n, t_tick_y // n, t_tick_area // n
    tick = (tick_x, tick_y)
    print(tick)

    # Get blue-circles info
    t_circ_x, t_circ_y = [[] for _ in range(n*n)], [[] for _ in range(n*n)]
    for _ in range(n):
        t = find_circ()
        #print(t)
        for ind, element in enumerate(t):
            x_p, y_p, z_p = get_point((element.cx(), element.cy()), L)
            if -65 <= y_p <= 65 and -82 <= z_p <= 82:
                t_circ_x[ind].append(element.cx())
                t_circ_y[ind].append(element.cy())

    blue_circ_x = list(sum(i) // len(i) for i in t_circ_x if len(i) != 0)
    blue_circ_y = list(sum(i) // len(i) for i in t_circ_y if len(i) != 0)
    blue_circs = list(zip(blue_circ_x, blue_circ_y))
    print(blue_circs)
    coords = []
    for i in blue_circs:
        point_x, point_y, point_z = get_point(i, L)
        coord_y = point_y // 20
        point_z -= 2
        coord_z = point_z // 20
        coords.append(coord_y + 1, coord_z - 1)
    #print(blue_circs)

    # Now sort circles in true plan
    blue_circs = sorted(blue_circs, key=lambda x: -1 * get_point(x, L)[1] // 20, math.sqrt(
        (x[0] - tick[0]) ** 2 + (x[1] - tick[1]) ** 2))
    sort_circles(blue_circs, tick)

    green_led.on()
    pyb.delay(2000)
    green_led.off()

    # Solve the problem
    for c in coord:
        point_y = c * 20 - 5
        point_z = c * 20 + 5


def exp():
    #green_led.on()
    for _ in range(n):
        L = run_middle_arifm(dist())
    print(L)
    t_circ_x, t_circ_y = [[] for _ in range(n * 2)], [[] for _ in range(n * 2)]
    #for i in range(100):
        #img = sensor.snapshot()
        #pyb.delay(10)
    for _ in range(1):
        t = find_circ()
        for ind, element in enumerate(t):
            ...
if __name__ == '__main__':
    #exp()
    main()
