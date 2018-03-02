#!/usr/bin/python

import os
import random
from network import DSRC_Network
from node import DSRC_Node, State

from config import *

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

    while(1):

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
        if (clock.time > END_TIME):
            exit(1)

        clock.tick()


main()

