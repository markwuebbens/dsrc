###############################################################################
#GLOBAL DEFINITIONS
###############################################################################
US_WEIGHT = 1000000
MEGA_BIT_WEIGHT = 1000000

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





