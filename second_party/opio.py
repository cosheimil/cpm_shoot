#!/usr/bin/python3
"""
  This is a clone of the 'gpio/WiringPi' project, written specifically for the
  OrangePi i96.

  Not all of gpio is re-implemented. The 'mode' command allows the user to 
  select any pin a GPIO or its special-funtion (i2c, spi, uart, pcm, etc)

  Pat Beirne <patb@pbeirne.com>

  Implemented:
    gpio read <gpio pin number>    => displays a value, returns 0 on success
    gpio write <gpio pin number> <value>    # set a pin high or low
    gpio mode [in | out | alt]	    # set the pin for in/out or special-function
    gpio readall                    # display all current pin settings
                                    # and the pin assignments on the 40 pin i96
    gpio readallx                   # similar to above, but shows RDA pinout
    gpio exports                    # simply dump the state of all the exports
                                    # which exist	
    gpio leds                       # like readall, but for LEDs, switches  
                                    # and other on-board devices 

  NOTE: pin numbers are always gpio numbers.
     use 'readall' to see the connector assignment

  By default, the 'mode' function will create/delete an export. By default, 
    the 'read' and 'write' function will set the mode and create an export.
    To disable this default, use the '-d' option.

  Variable plan: functions which are "is_" or "has_" return boolean
    functions which involve 'in' 'out' 'alt' pass-&-return strings
    functions which involve values pass-&-return ints....-1 means invalid
    gpio is always a short int

  Attack plan:
    mode set: check iomux, then create-&-use export
        -d set: check iomux, then low-level set
    read: check iomux, then check export, then use export
        -d: check iomux, then low-level read
    write: check iomux, then check export then set mode=out then use export
        -d: check iomux, then set direction=out, tne low-level write
    NOTE: 'read' and 'write' will auto-set the GPIO mode and disable 'alt'
    NOTE: 'read' and 'write' will auto-set the GPIO mode and disable 'alt'
  
  Classes: GPIO to access a pin through the export-gpio methods
     GPIO_DIRECT to access only through low-level calls
     read/write/mode will use GPIO unless the -d flag is used
     exports will always use GPIO
     readall/readallx/leds will use GPIO_DIRECT
"""
from mmap import mmap
from struct import pack, unpack
import os, sys, argparse, pathlib, re, logging

VERSION = "2.2"

############ board specific

class Board:
  def __init__(self,full_name,short_name,config_file):
    self.name = full_name
    self.short_name = short_name
    self.config_file = config_file
  def __repr__(self):
    return self.name

board_i96 = Board("OrangePi i96",  "OrangePi i96", "/etc/OrangePi-i96")


# pins, arranged according to i96 connector
# i96 label, rda_port number, pio number, rda special function
board_i96.PINS = ( 
  ("GND",		"",	   -1,	"", ""),  # 1
  ("GND",		"",	   -1,	"", ""),
  ("UART2.CTS", "B8",  40,	"CTS", "ttyS1.cts"),
  ("PWR_BTN_N", "",	   -1,	"", ""),
  ("UART2.TX",  "C8", 104,  "TX", "ttyS1.tx"),
  ("RST_BTN_N", "",    -1,  "1.4v", ""),    
  ("UART2.RX",	"C7", 103,  "RX", "ttyS1.rx"),
  ("SPI2.CLK",	"A2", 	2,  "CLK","spi2.clk"),
  ("UART2.RTS", "B9", 	41, "RTS","ttyS1.rts"),
  ("SPI2.DI", 	"A4", 	4,  "DI", "spi2.di"), # 10
  ("UART1.TX",	"A14", 14,  "TX", "ttyS0.tx"), 
  ("SPI2.CS",	"A6",	6,	"CS", "spi2.cs"),
  ("UART1.RX",	"C6", 102,  "RX", "ttyS0.rx"),
  ("SPI2.DO", 	"A3",   3,  "DO", "spi2.do"),
  ("I2C2.SCL",	"A0", 	0,  "SCL", "i2c-1.scl"),
  ("I2S.LRCK",	"A10", 10,  "LRCK", "pcm.fp"), 
  ("I2C2.SDA",	"A1",	1,	"SDA", "i2c-1.sda"),
  ("I2S.BCK",	"A9", 	9,  "BCK", "pcm.clk"),
  ("I2C3.SCL", 	"B6", 	38, "SCL", "i2c-2.scl"),
  ("I2S.DO", 	"A13",  13, "DO",  "pcm.do"), # 20 
  ("I2C3.SDA",	"B7",	39, "SDA", "i2c-2.sda"),
  ("I2S.DI",	"A11",  11, "DI",  "pcm.di"),
  ("GPIO.A",	"A15",	15, "CTS", "ttyS0.cts"), 
  ("GPIO.B", 	"A20",	20, "LCD", "lcd"),
  ("GPIO.C",	"B24",	56, "ROM", "n/a"), 
  ("GPIO.D", 	"D2",	66, "CTS", "ttyS2.cts"),
  ("GPIO.E",	"D3",	67, "RTS", "ttyS2.rts"), 
  ("GPIO.F", 	"A22",	22, "LCD", "lcd"),
  ("GPIO.G",	"A30",	30, "LCD", "lcd"), 
  ("GPIO.H", 	"A29",	29, "LCD", "lcd"), # 30
  ("GPIO.I",	"A28",	28, "LCD", "lcd"), 
  ("GPIO.J", 	"A27",	27, "LCD", "lcd"),
  ("GPIO.K",	"A26",	26, "LCD", "lcd"), 
  ("GPIO.L", 	"A25",	25, "LCD", "lcd"),
  ("V_PAD", 	"", 	-1, "1.8v", ""),
  ("SYS_DCIN",	"",	    -1, "n/c",  ""),
  ("VDD_IN",	"", 	-1, "5V",   ""),
  ("SYS_DCIN",	"",	    -1, "n/c",  ""),
  ("GND", 		"", 	-1, "",     ""),
  ("GND", 		"", 	-1, "",     "") # 40
)	

board_i96.other = ( 
  ("LED2", "C30", 126, ""),
  ("LED3", "C29", 125, ""),
  ("LED5", "C5", 101, ""),
  ("J2", "C2", 98, "boot sd"),
  ("OTGPWR","A17",17,""),
#  ("DBG_TX","D1",65,"TX"),
#  ("DBG_RX","D0",64,"RX"),
)

########################## cpu specific
class Cpu:
  def __init__(self,name):
    self.name = name

RDA_PORTC_IOMUX = 0x11a09008
RDA_PORTA_IOMUX = 0x11a0900c
RDA_PORTB_IOMUX = 0x11a09010
RDA_PORTD_IOMUX = 0x11a09014

cpu_rda = Cpu("RDA8810")
cpu_rda.IOMUX_ADDRESSES = (RDA_PORTA_IOMUX, RDA_PORTB_IOMUX, RDA_PORTD_IOMUX, RDA_PORTC_IOMUX)

cpu = cpu_rda

GPIO_PER_PORT = 32

PAGE_MASK   = ~0xFFF
PAGE_OFFSET = 0xFFF

SYS_PATH = "/sys/class/gpio/"

def pin_has_export(gpio):
  return pathlib.Path('/sys/class/gpio/gpio{}'.format(gpio)).exists()

#################### memory access

def mem_set(address, bitmask, value):
  try:
    with open("/dev/mem","w+b") as m:
      mem = mmap(m.fileno(), 32, offset = address & PAGE_MASK)
      address &= PAGE_OFFSET 
      data = unpack("<L",mem[address:address+4])[0] 
      logging.debug("mem_set: current data is {} mask is {} value is {}".format(hex(data),hex(bitmask),value))
      if value:
        data |= bitmask
      else:
        data &= ~bitmask
      logging.debug("mem_set: resulting data is {}".format(hex(data)))
      mem[address:address+4] = pack("<L",data)
  except PermissionError:
    print("failed to open /dev/mem.....you must execute this script as root")
    sys.exit(1)

def mem_get(address, bitmask):
  try:
    with open("/dev/mem","r+b") as m:
      mem = mmap(m.fileno(), 32, offset = address & PAGE_MASK)
      address &= PAGE_OFFSET 
      return unpack("<L",mem[address:address+4])[0] & bitmask
  except PermissionError:
    print("failed to open /dev/mem.....you must execute this script as root")
    sys.exit(1)

############################ pin access
""" decide which kind of GPIO """
def GPIO_factory(gpio,direct):
  if direct:
    return GPIO_DIRECT(gpio)
  else:
    return GPIO(gpio)

""" via the gpio/export system """
class GPIO:
  ''' this object owns a pin, assures it has an export and accesses it through the gpio-export mechanism'''
  def __init__(self, gpio):
    self.gpio = gpio
    self.set_iomux(True)
    create_export(gpio)

  def get(self):
    # logging.debug("GPIO.get")
    # we don't care about the export/direction
    with open(SYS_PATH + "gpio{}/value".format(self.gpio)) as f:
      r = int(f.read())
    # logging.debug("pin_read of {} returns {}".format(self.gpio,r))
    return r
  def set(self, value):
    # logging.debug("GPIO.set {} {}".format(self.gpio, value))
    self.set_mode('out')
    with open(SYS_PATH + "gpio{}/value".format(self.gpio),"w+b") as f:
      f.write(bytes(str(value),"utf-8"))

  def set_mode(self,mode_string):
    with open('/sys/class/gpio/gpio{}/direction'.format(self.gpio),'w') as f:
      f.write(mode_string) 
  def get_mode_value(self):
    with open('/sys/class/gpio/gpio{}/direction'.format(self.gpio)) as f:
      return f.read().strip(), self.get()

  def set_iomux(self, gpio_mode):
    ''' set value=True for this pin to be GPIO, 
       False for this pin to be special function'''
    # logging.debug("GPIO: set iomux for pin {} to {}".format(self.gpio,gpio_mode))
    port_group = self.gpio // GPIO_PER_PORT
    port_offset = self.gpio % GPIO_PER_PORT
    mem_set(cpu.IOMUX_ADDRESSES[port_group], 1 << port_offset, gpio_mode)
    if gpio_mode == False:
      # logging.debug("GPIO.set_iomux with mode {}".format(gpio_mode))
      remove_export(self.gpio)
  def get_iomux(self):
    ''' returns 1 when it's in GPIO mode, 0 for alt mode '''
    # logging.debug("GPIO check the IOMUX for gpio {}".format(self.gpio))
    port_group = self.gpio // GPIO_PER_PORT
    port_offset = self.gpio % GPIO_PER_PORT
    # logging.debug("check IOMUX at address {}".format(hex(cpu.IOMUX_ADDRESSES[port_group])))
    return mem_get(cpu.IOMUX_ADDRESSES[port_group], 1 << port_offset)
  
  def __repr__(self):
    return("gpio"+str(self.gpio))       

class GPIO_DIRECT(GPIO):
  def __init__(self,gpio):
    self.gpio = gpio

  def set(self,value):
    # logging.debug("GPIO_DIRECT.set {} value: {}".format(self.gpio,value))
    if self.get_iomux()==0:
      self.set_iomux(1)
      self.set_mode('out')
    low_level_write(self.gpio,IO_DATA,value)
  def get(self):
    if self.get_iomux() == 0:
      self.set_iomux(1)
      self.set_mode('in')
    return low_level_read(self.gpio,IO_DATA)

  def get_mode_value(self):
    iomux = self.get_iomux() 
    if not iomux:
      return 'alt','?' 
    d = low_level_read(self.gpio, IO_DIR)
    m = 'in' if d else 'out'
    if not pin_has_export(self.gpio):
       m = m+'*'
    return m, low_level_read(self.gpio,IO_DATA)  

  def set_mode(self, mode_string):
    low_level_set_mode(self.gpio, mode_string);

  def set_iomux(self, gpio_mode):
    super().set_iomux(gpio_mode)

def create_export(gpio):
  ''' make sure this gpio has an export set in the /sys/class/gpio dir '''
  if not pin_has_export(gpio):
    with open(SYS_PATH + 'export','w') as f:
      f.write(str(gpio))
    if not pin_has_export(gpio):
      print("could not create the gpio-export for pin {}".format(gpio))
      print("perhaps you should run this program as root")
      sys.exit(1)
  return

def remove_export(gpio):
  if pin_has_export(gpio):
    with open(SYS_PATH + 'unexport','w') as f:
      f.write(str(gpio))
  return
 
################## low level pin control ################
""" bypass the gpio/export system """ 
PORTA_IOBASE = 0x20930000
PORTB_IOBASE = 0x20931000
PORTC_IOBASE = 0x11a08000
PORTD_IOBASE = 0x20932000
IOBASE_ADDRESSES = (PORTA_IOBASE, PORTB_IOBASE, PORTD_IOBASE, PORTC_IOBASE)

IO_DIR = 0   # [0=out,1=in] +0 direct access, +4 = clr-reg(out), +8 = set-reg(in) 
IO_DATA = 0xc # +0 direct access, +4 for set-reg, +8 for clr-reg

def low_level_read(gpio, address_offset):
  port_group = gpio // GPIO_PER_PORT
  port_offset = gpio % GPIO_PER_PORT
  address = IOBASE_ADDRESSES[port_group] + address_offset
  r = mem_get(address, 1 << port_offset)
  logging.debug("low_level_read of address {} and bit {} returns {}".format(hex(address),port_offset,hex(r)))
  return 1 if r else 0

def low_level_write(gpio, address_offset, data):
  port_group = gpio // GPIO_PER_PORT
  port_offset = gpio % GPIO_PER_PORT
  address = IOBASE_ADDRESSES[port_group] + address_offset
  mem_set(address, 1 << port_offset, data)
  
def low_level_set_mode(gpio, mode):
  if mode == 'alt':
    print("illegal call to low_level_set_mode")
    sys.exit(1)
  low_level_write(gpio, IO_DIR, 0 if mode=='out' else 1)
  
def low_level_get_mode(gpio):
  return low_level_read(gpio, IO_DIR)  

######################### detect board ###################
# the 2gio has the B3 pin pulled up
# the i96 board leaves the B3 pin floating
B3 = 35
board = board_i96

def board_auto_sense(args):
  global board
  if args.cmd in {"readll","readallx","status","statusx","leds","exports"}:
    if pathlib.Path(board_2g.config_file).exists() or args.op2giot:
      board = board_2g
    elif pathlib.Path(board_i96.config_file).exists() or args.i96:
      board = board_i96
    else:
      low_level_set_mode(B3, "out")
      low_level_write(B3, IO_DATA, 1)
      low_level_set_mode(B3, "in")
      a = low_level_read(B3, IO_DATA)
      low_level_set_mode(B3, "out")
      low_level_write(B3, IO_DATA, 0)
      low_level_set_mode(B3, "in")
      b = low_level_read(B3, IO_DATA)
      board = board_2g if b else board_i96
      print("Board auto-detect found {}. To skip auto-detect, create a file named {}".format(board.short_name,board.config_file))

########################### actions #######################

def do_readall():
    exports_dirty = False
    print("""
+-----+-----+----------+------+-+ {} +-+------+----------+-----+-----+
| gpio| alt | i96 Name | Mode | V | Physical | V | Mode | i96 Name | alt | gpio|
+-----+-----+----------+------+---+----++----+---+------+----------+-----+-----+""".format(
       board.short_name))
    for i in range(20):
      left_gpio = board.PINS[2*i][2]
      if left_gpio != -1:
        left_g = GPIO_DIRECT(left_gpio)
        left_mode, left_value = left_g.get_mode_value()
        left_gpio_str = str(left_gpio) 
        if '*' in left_mode: exports_dirty = True
      else:
        left_gpio_str = left_mode = left_value = ""      

      right_gpio = board.PINS[2*i+1][2]
      if right_gpio != -1:
        right_g = GPIO_DIRECT(right_gpio)
        right_mode, right_value = right_g.get_mode_value()
        right_gpio_str = str(right_gpio) 
        if '*' in right_mode: exports_dirty = True
      else:
        right_gpio_str = right_mode = right_value = ""
      left_value,right_value = str(left_value),str(right_value)

      print("| {:3s} | {:4s}| {:9s}| {:4s} | {:1s} | {:2d} || {:2d} | {:1s} | {:4s} | {:9s}| {:4s}| {:3s} |".format(
        left_gpio_str,board.PINS[2*i][3],board.PINS[2*i][0],
        left_mode,left_value,2*i+1,
        2*i+2,right_value,right_mode,board.PINS[2*i+1][0],
        board.PINS[2*i+1][3],right_gpio_str))
    print("+-----+-----+----------+------+---+----++----+---+------+----------+-----+-----+")
    if exports_dirty:
      print("Note: *these pins are set to GPIO mode but do NOT have exports in /sys/class/gpio")

def do_exports():
  print("GPIO Pins  Mode Value  Located")
  for f in os.listdir(SYS_PATH):
    if re.match('gpio\d',f):
      gpio = GPIO(int(f[4:]))
      m,v = gpio.get_mode_value()
      iop = ""
      for i in range(len(board.PINS)):
        if board.PINS[i][2]==gpio.gpio: 
          iop = (board.short_name + " I/O: {}").format(i+1)
          break
      for i in range(len(board.other)):
        if board.other[i][2]==gpio:
          iop = board.other[i][0]
          break
      print("{:>9s}  {:3}  {:<6} {}".format(f,m,v,iop))

def do_leds():
    print("+------+-------+------+-----+")
    print("| gpio | func  | mode |value|")
    print("+------+-------+------+-----+")
    for p in board.other:
      #print("led function:", p)
      g = GPIO_DIRECT(p[2])
      m,v = g.get_mode_value()
      print("| {:3}  | {:6}| {:4} |  {:1}  |".format(
        p[2],p[0],m,v))
    print("+------+-------+------+-----+")

def check_gpio_valid(gpio):
  if gpio == None or gpio<0 or gpio>127:
    # print("the {} command requires a gpio pin number".format(args.cmd))
    sys.exit(1)
    
def do_read():
  logging.debug("do_read: %d",args.gpio)
  check_gpio_valid()
  gpio = args.gpio
  g = GPIO_factory(gpio,args.direct)
  return g.get()

# gpio is a pin number, extra is value
def do_write(gpio, extra):
  # logging.debug("do_write: %d %s",args.gpio, args.extra)

  check_gpio_valid()
  g = GPIO_factory(gpio, False)
  if args.extra in ('1', 'on', 'ON'):
    v = 1
  elif args.extra in ('0', 'off', 'OFF'):
    v = 0
  else:
    # print("the 'write' command requires a 2nd argument, either 0 or 1")
    sys.exit(1)
  g.set(v)

def do_mode():
  logging.info("do_mode %d %s", args.gpio, args.extra)
  logging.info("the -d flag is {}".format(args.direct))
  check_gpio_valid()

  if args.extra == None:
    m,v = GPIO_DIRECT(args.gpio).get_mode_value()
    print(m)    
    return

  if args.extra == "alt": 
    args.direct = True
  gpio = GPIO_factory(args.gpio,args.direct)
  if args.extra in ('in','out'):
    logging.info("set mode: %s",args.extra)
    gpio.set_iomux(True)
    gpio.set_mode(args.extra)
  elif args.extra=='alt':
    logging.info("set alt mode")
    gpio.set_iomux(False)

def do_readallx():
    exports_dirty = False
    print("""
+-----+-----+----------+------+-+ {} +-+------+----------+-----+-----+
| gpio| RDA | alt name | Mode | V | Physical | V | Mode | alt name | RDA | gpio|
+-----+-----+----------+------+---+----++----+---+------+----------+-----+-----+""".format(
       board.short_name))
    for i in range(20):
      left_gpio = board.PINS[2*i][2]
      if left_gpio != -1:
        left_g = GPIO_DIRECT(left_gpio)
        left_mode, left_value = left_g.get_mode_value()
        left_gpio_str = str(left_gpio) 
        if '*' in left_mode: exports_dirty = True
      else:
        left_gpio_str = left_mode = left_value = ""      

      right_gpio = board.PINS[2*i+1][2]
      if right_gpio != -1:
        right_g = GPIO_DIRECT(right_gpio)
        right_mode, right_value = right_g.get_mode_value()
        right_gpio_str = str(right_gpio) 
        if '*' in right_mode: exports_dirty = True
      else:
        right_gpio_str = right_mode = right_value = ""
      left_value,right_value = str(left_value),str(right_value)

      print("| {:3s} | {:4s}| {:9s}| {:4s} | {:1s} | {:2d} || {:2d} | {:1s} | {:4s} | {:9s}| {:4s}| {:3s} |".format(
        left_gpio_str,board.PINS[2*i][1],board.PINS[2*i][4],
        left_mode,left_value,2*i+1,
        2*i+2,right_value,right_mode,board.PINS[2*i+1][4],
        board.PINS[2*i+1][1],right_gpio_str))
    print("+-----+-----+----------+------+---+----++----+---+------+----------+-----+-----+")
    if exports_dirty:
      print("Note: *these pins are set to GPIO mode but do NOT have exports in /sys/class/gpio")
    print("Note: the alt names are based on the Linux naming scheme")

args = None

if __name__ == "__main__":
  #logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
  #logging.basicConfig(stream=sys.stderr, level=logging.INFO)
  parser = argparse.ArgumentParser(description = "Access GPIO on the OrangePi RDA boards")
  parser.add_argument('-v','--version', action='version', 
   version="opio "+VERSION+" -- python rewrite of gpio; by Pat Beirne")
  parser.add_argument('cmd',help="one of: read/in, write/out, mode, readall/status, readallx/statusx, leds, exports")
  parser.add_argument('gpio',nargs='?',type=int,help="gpio number 0...126")
  parser.add_argument('extra',nargs='?')
  parser.add_argument('-d',"--direct",help="use low-level access",action="store_true")
  parser.add_argument('-2',"--op2giot",help="configure for OrangePi 2G-iot [disable auto-detect]",action="store_true")
  parser.add_argument('-9',"--i96",help="configure for OrangePi i96 [disable auto-detect]",action="store_true")
  args = parser.parse_args()

  board_auto_sense(args)
 
  switcher = {"readall":do_readall, 
         "readallx":do_readallx,
         "status":do_readall, 
         "statusx":do_readallx, 
         "leds":do_leds,
         "mode":do_mode,
         "read":do_read,
         "write":do_write,
         "in":do_read,
         "out":do_write,
         "exports":do_exports}
  f = switcher.get(args.cmd)
  if not f:
    print("the available commands are:", ", ".join(sorted(list(switcher.keys()))))
    print("function",args.cmd,"not found")
    sys.exit(1)
  f()

  