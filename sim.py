#!/usr/bin/python

import os
import random
from network import DSRC_Network
from node import DSRC_Node, State
from time import strftime

from config import *

node_id = 0
log_dir = strftime("%d%m%Y_%H%M%S") + "_log/"
os.mkdir(log_dir)

class Clock():
    def __init__(self):
        self.time = 0.0
        self.ticks = 0
        self.dt = SLOT_TIME

    def tick(self):
        self.time += self.dt
        self.ticks += 1
        #print "TICK! {}".format(self.time)

    def timenow(self):
        return self.time

def generate_node(clock, network, init_x = 0):

    global node_id
    global sim_dir
    coin_toss = random.random()

    density_weight = clock.dt * AVG_SPEED * VEH_DENSITY #s * m/s * veh/m

    if (coin_toss < density_weight):

        velocity = random.uniform(AVG_SPEED-SPEED_DELTA, AVG_SPEED+SPEED_DELTA)
        node = DSRC_Node(node_id, init_x, velocity, clock, log_dir)
        node_id += 1

        network.add_node(node)

def generate_initial_traffic(clock, network):
    marker = ROAD_LIMIT;

    while (marker > 0):
        node = generate_node(clock, network, marker)

        marker -= clock.dt * AVG_SPEED

def main():

    clock = Clock()

    this_network = DSRC_Network(clock, log_dir)
    generate_initial_traffic(clock, this_network)

    num_finished = 0

    while(1):
        #print "time:{:.6f}, timenow:{:.6f}".format(clock.time, clock.timenow())

        #generate and add new nodes
        generate_node(clock, this_network)

        #Execute one logical step of the simulation
        # -Each node: Moves forward logically in time and space
        # -'Finished' nodes are removed from the network and returned
        finished_nodes = this_network.step_sim()
        num_finished += len(finished_nodes)

        #Network arbitrates message tx'ing and collision for curr state
        # -First sorts tx_nodes and all_nodes lists sorted here
        # -Each node: Receives any valid transmission
        #             Receives it's current local channel state
        #
        # MUST BE CALLED BEFORE network.transition_sim()!
        this_network.arbitrate_channel_conditions()

        #Network elements increment logically in time and space
        # -Each node: Executes (cs -> ns) in the DSRC FSM according to local
        #   conditions
        this_network.transition_sim()

        #Finish at some point...
        if (clock.timenow() > END_TIME):
            exit(1)

        clock.tick()


main()

