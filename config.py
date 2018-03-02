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
END_TIME = 1.0 * 4 #s

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



def print_intro(clock):
    print "\n<--- HELLO. --->"
    print "We are simulating a straight, uni-directional highway which is {} m long".format(ROAD_LIMIT)
    print "The traffic density is set at {} veh/m".format(VEH_DENSITY)
    print "Vehicles are traveling uniformly between {} and {} m/s".format(AVG_SPEED-SPEED_DELTA, AVG_SPEED+SPEED_DELTA)
    print "The simulation runs at increments of {} s".format(clock.dt)
    print "Vehicles are transmitting safety beacons over a {} m range".format(TX_RANGE)
    print "msg len = {} bits, tx_rate = {} bps, time to tx = {} s".format(PACKET_SIZE, TX_RATE, PACKET_SIZE/TX_RATE)
    print "The CW window is set to: 0 <= CW <= {} s".format(CW_NOMINAL*SLOT_TIME)
    print "<------------------------->"

def print_summary(clock, network, num_finished):
    print "\n<--- In Summary: --->"
    print "Simulated {} nodes for a logical time of {} seconds".format(network.total_cnt, clock.time)
    print "{} nodes drove past the limit of the sim".format(num_finished)
    print "<--- GOODBYE. --->"

