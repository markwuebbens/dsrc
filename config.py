###############################################################################
#GLOBAL DEFINITIONS
###############################################################################
US_WEIGHT = 1000000
MEGA_BIT_WEIGHT = 1000000

#Simulation and road defs
AVG_SPEED = 20 #m/s
SPEED_DELTA = 4  #m/s
VEH_DENSITY = .165 # veh/m

ROAD_LIMIT = 500 #m
END_TIME = 1.0 * 5 #s

#Network defs
SLOT_TIME_US = 13.0 #us
SLOT_TIME = SLOT_TIME_US / US_WEIGHT #s
IFS_TIME_US = 58.0 #us
IFS_TIME =  IFS_TIME_US / US_WEIGHT #s

BEACON_FREQ = 10.0 #hz
BEACON_PERIOD = 1.0 / BEACON_FREQ #s

PACKET_SIZE = 500 * 8  #bits
TX_RATE = 3.0 * MEGA_BIT_WEIGHT #bps
TX_RATE_US = TX_RATE / US_WEIGHT #bits per us
TX_RANGE = 50 #m

CW_BASE = 2
CW_POWER = 8 #4, 6, 8, 10
CW_NOMINAL = CW_BASE ** CW_POWER #units of 'slots'

