#!/usr/bin/python

import os
import sys
import argparse
import random
from time import strftime
from network import DSRC_Network
from logger import DSRC_Sim_Logger
from config import SLOT_TIME, BEACON_PERIOD

#Road definitions
Road_Limit = 500.0 #m

#Sim definitions
End_Time = 5.0 * 60 #s

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
        assert ((CW_POWER > 0.0) and (2**(CW_POWER*1.0) * SLOT_TIME < BEACON_PERIOD / 10.0)), "CW_POWER out of bounds {}".format(CW_POWER)

        self.cw_power = CW_POWER
        self.cw_nom = 2 ** (CW_POWER * 1.0) #units of slots
        self.cw_max_delay = self.cw_nom * SLOT_TIME #units of seconds

    def gen(self):
        val = random.uniform(0, self.cw_max_delay)
        assert val, "gen {}".format(val)
        return val

    def max_delay(self):
        return self.cw_max_delay


def main():

    global Road_Limit, End_Time

    parser = argparse.ArgumentParser(description='A Simulator')
    parser.add_argument("tx_range",
                        help="Transmision range (~10-100)(m)",
                        type=float)
    parser.add_argument("cw_power",
                        help="The exponent to determine CW backoff time",
                        type=float)
    parser.add_argument("veh_density",
                        help="Rho, the average vehicular density (veh/m)",
                        type=float)
    parser.add_argument("avg_speed", help="Avg vehicular speed (m/s)", type=float)
    parser.add_argument("speed_delta", help="The delta speed value (m/s)", type=float)
    args = parser.parse_args()

    try: #Input sanitization

        # Sanitize TX_RANGE
        #Max tx_range of 1 fifth of the road length
        assert ((args.tx_range > 0.0) and (args.tx_range * 5.0 < Road_Limit)),\
               "TX_RANGE {} {}".format(args.tx_range, Road_Limit)

        # Sanitize  AVG_SPEED
        #Max speed of ~220 mph
        assert ((args.avg_speed > 0.0) and (args.avg_speed < 100.0)), "AVG_SPEED"

        # Sanitize  SPEED_DELTA
        #totally arbitrary max speed_delta... :3
        assert ((args.speed_delta > 0.0) and (args.speed_delta < 40)), "SPEED_DELTA"

        # Sanitize  VEH_DENSITY
        #Max denisty of one vehicle per every meter... (still kind of arbitrary)
        assert ((args.veh_density > 0.0) and (args.veh_density < 1.0)), "VEH_DENSITY"

        # Sanitize  CW_POWER
        #Max power arbitrarily 1000
        assert ((args.cw_power > 0.0) and (args.cw_power < 1000))

        #Init a CW generator which will describe the CW characteristics of this sim
        cw_generator = CW_Generator(args.cw_power)


    except Exception as e:
        print e.message, e.args
        print "FUUUUUCK"
        sys.exit

    else:

        Log_Dir = "{}_{:n}m_{:n}mps_{:.4f}vpm_{:.6f}s/".format(\
                  strftime("%m%d_%H%M%S"),\
                  args.tx_range, args.avg_speed,\
                  args.veh_density, cw_generator.max_delay())

        #IMPORTANTE! - Create the output dir
        os.mkdir(Log_Dir)

        num_finished = 0

        #Init the system clock
        sysclock = Clock()

        #Init the simulated network, (creates a road filled with vehicles)
        this_network = DSRC_Network(sysclock, Log_Dir,\
                                    args.avg_speed, args.speed_delta, args.veh_density,\
                                    cw_generator, args.tx_range, Road_Limit)

        #Init a logger for the simulation
        this_sim_logger = DSRC_Sim_Logger(sysclock.stepsize(),\
                                    strftime("%m%d_%H%M%S"),\
                                    Log_Dir, args.veh_density, args.tx_range,\
                                    cw_generator.max_delay(),\
                                    args.avg_speed, args.speed_delta, Road_Limit)


        #Run the network until end times come
        while(sysclock.timenow() < End_Time):

            #Execute one logical step of the simulation
            finished_nodes = this_network.step()
            num_finished += len(finished_nodes)
            sysclock.tick()


        #Log some summary values
        this_sim_logger.write_summary(sysclock.timenow(),\
                                        num_finished,\
                                        strftime("%m%d_%H%M%S"))

        print "GG No RE"
        sys.exit()

main()

