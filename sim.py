#!/usr/bin/python

import os
import sys
import argparse
import random
from time import strftime
from network import DSRC_Network
from logger import DSRC_Sim_Logger
from config import SLOT_TIME, BEACON_PERIOD, ROAD_LIMIT, END_TIME

class Clock():
    def __init__(self):
        self.time = 0.0
        self.ticks = 0
        self.dt = SLOT_TIME

    def tick(self):
        self.time += self.dt
        self.ticks += 1

    def timenow(self):
        return self.time

    def stepsize(self):
        return self.dt

class CW_Generator():
    def __init__(self, CW_POWER):
        assert (CW_POWER >= 2) and (2**(1.0*CW_POWER) * SLOT_TIME < BEACON_PERIOD / 10.0),\
        "CW_POWER out of bounds {}".format(CW_POWER)

        self.cw_power = CW_POWER
        self.cw_nom = 2.0 ** (CW_POWER * 1.0) #units of slots
        self.cw_max_delay = self.cw_nom * SLOT_TIME #units of seconds

    def gen(self):
        val = random.uniform(0, self.cw_max_delay)
        assert val, "gen {}".format(val)
        return val

    def max_delay(self):
        return self.cw_max_delay


def init_network(network, clock, avg_speed):

    #Fill the length of the road with vehicles
    marker = ROAD_LIMIT;
    while (marker > 0):

        network.generate_node(marker)
        marker -= clock.stepsize() * avg_speed

def main():

    parser = argparse.ArgumentParser(description='A Simulator')
    parser.add_argument("tx_range",
                        help="Transmision range (~10-100)(m)",
                        type=float)
    parser.add_argument("cw_power",
                        help="The exponent to determine CW backoff time",
                        type=float)
    parser.add_argument("veh_density",
                        help="The average vehicular density (veh/m)",
                        type=float)
    parser.add_argument("avg_speed", help="Avg vehicular speed (m/s)", type=float)
    parser.add_argument("speed_delta", help="The delta speed value (m/s)", type=float)
    args = parser.parse_args()

    try: #Input sanitization

        # Sanitize TX_RANGE
        #Max tx_range of 1 fifth of the road length
        assert ((args.tx_range > 0.0) and (args.tx_range * 5.0 < ROAD_LIMIT)),\
               "TX_RANGE {} {}".format(args.tx_range, ROAD_LIMIT)

        # Sanitize  AVG_SPEED
        #Max speed of ~220 mph
        assert ((args.avg_speed > 0.0) and (args.avg_speed < 100.0)), "AVG_SPEED"

        # Sanitize  SPEED_DELTA
        #totally arbitrary max speed_delta... :3
        assert ((args.speed_delta > 0.0) and (args.speed_delta < 40)), "SPEED_DELTA"

        # Sanitize  VEH_DENSITY
        #Max denisty of one vehicle per every meter... (still kind of arbitrary)
        assert ((args.veh_density > 0.0) and (args.veh_density < 1.0)), "VEH_DENSITY"

        #Init a CW generator which will describe the CW characteristics of this sim
        #Generator sanitizes it's own input
        cw_generator = CW_Generator(args.cw_power)


    except Exception as e:
        print e.message, e.args
        print "Failed to parse inputs... :("
        sys.exit

    else:

        #Create the directory where we will log results
        Log_Dir = "{}_{:n}m_{:n}mps_{:.4f}vpm_{:.6f}s/".format(\
                  strftime("%m%d%H%M%S"),\
                  args.tx_range, args.avg_speed,\
                  args.veh_density, cw_generator.max_delay())
        #IMPORTANTE! - Create the output dir
        os.mkdir(Log_Dir)

        num_finished = 0

        #Init the system clock
        sysclock = Clock()

        #Create the network
        this_network = DSRC_Network(sysclock, Log_Dir,\
                                    args.avg_speed, args.speed_delta, args.veh_density,\
                                    cw_generator, args.tx_range)

        #Fills the road with vehicles
        init_network(this_network, sysclock, args.avg_speed)

        #Init a logger for the simulation
        this_sim_logger = DSRC_Sim_Logger(sysclock.stepsize(),\
                                    strftime("%m%d%H%M%S"),\
                                    Log_Dir, args.veh_density, args.tx_range,\
                                    cw_generator.max_delay(),\
                                    args.avg_speed, args.speed_delta,\
                                    ROAD_LIMIT)

        #######################################################################
        #Run the network until end times come
        #######################################################################
        while(sysclock.timenow() < END_TIME):

            sysclock.tick()
            #Execute one logical step of the simulation
            num_finished += len(this_network.step())


        #Log some summary values
        this_sim_logger.write_summary(sysclock.timenow(),\
                                        num_finished,\
                                        strftime("%m%d%H%M%S"))

        sys.exit()

main()

