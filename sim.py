#!/usr/bin/python

import os
import random
from network import DSRC_Network
from node import DSRC_Node, State

from config import *

#from network import DSRC_Network
#from node import DSRC_Node

node_id = 0

class Clock():
    def __init__(self):
        self.time = 0.0
        self.ticks = 0
        self.dt = SLOT_TIME

    def tick(self):
        self.time += self.dt
        self.ticks += 1

def generate_node(clock, network, init_x = 0):

    global node_id
    coin_toss = random.random()

    density_weight = clock.dt * AVG_SPEED * VEH_DENSITY #s * m/s * veh/m

    if (coin_toss < density_weight):

        velocity = random.uniform(AVG_SPEED-SPEED_DELTA, AVG_SPEED+SPEED_DELTA)
        node = DSRC_Node(node_id, init_x, velocity, clock)
        node_id += 1

        network.add_node(node)

def generate_initial_traffic(clock, network):
    marker = 0;

    while (marker < ROAD_LIMIT - TX_RANGE):
        node = generate_node(clock, network, marker)

        marker += clock.dt * AVG_SPEED

def main():

    clock = Clock()

    this_network = DSRC_Network(clock)
    generate_initial_traffic(clock, this_network)

    num_finished = 0

    print_intro(clock)

    while(1):

        if (clock.time > END_TIME):
            #network.compute_and_display_final_stats()
            print_summary(clock, this_network, num_finished)
            exit(1)

        clock.tick()

        #generate and add new nodes
        generate_node(clock, this_network)

        #Network arbitrates message tx'ing and collision for curr state
        # (First sorts tx_nodes and all_nodes lists sorted here)
        # (Each node: Checks immediate for valid transmission)
        # (           Logs any successfull full packets recv'd)
        # (           Saves the local channel state)
        #
        # MUST BE CALLED BEFORE network.step_sim()!
        this_network.arbitrate_channel_conditions()

        #Network elements increment logically in time and space
        # (Each node: Executes (cs -> ns) in the DSRC FSM
        # (           Moves forward logically in time and space)
        # 'Finished' nodes are removed from the network and returned
        (finished_nodes, finished_msgs) = this_network.step_sim()

        num_finished += len(finished_nodes)

        if finished_msgs:
            print "> {:.6f}s\n".format(clock.time), finished_msgs,

main()

