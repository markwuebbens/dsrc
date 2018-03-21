import os
import math
import random

from node import State, DSRC_Node
from config import *
#from sim import SLOT_TIME, IFS_TIME, TX_RATE, TX_RANGE, SIM_LIMIT

class DSRC_Network:

    def __init__(self, clock):

        self.sys_clock = clock

        #Total num nodes simulated in the network
        self.total_cnt = 0

        #Set of ALL nodes in simulation
        self.all_nodes = set()

        #List of nodes which are tx'ing
        self.tx_nodes = set()


    ###########################################################################
    # Public Class Methods
    ###########################################################################
    """
    Add a node to the network
    """
    def add_node(self, node):
        self.all_nodes.add(node)
        self.total_cnt += 1

    """
    Perform one step of the top level traffic simulation
        -Each node in the network steps thru the dsrc fsm independently
        -Nodes increment in space and time, updating counters and state
        -Nodes considered 'finished' are removed and returned
    """
    def step_sim(self):

        finished_nodes = set()
        self.tx_nodes = set()

        for node in self.all_nodes:

            node.step_logical()

            #Aggregate 'finished' nodes
            if (node.is_finished):
                finished_nodes.add(node)

            #Aggregate nodes which are tx'ing right now
            elif (node.cs is State.tx):
                self.tx_nodes.add(node)

        #Remove finished nodes from the network
        self.all_nodes = self.all_nodes - finished_nodes

        return finished_nodes

    """
    Network informs each node of any valid transmissions and of local channel conditions
    """
    def arbitrate_channel_conditions(self):

        tx_sorted = sorted(self.tx_nodes, key=lambda node: node.x)
        len_txers = len(tx_sorted)

        all_sorted = sorted(self.all_nodes, key=lambda node: node.x)
        len_all = len(all_sorted)

        def _find_lo_tx_i(this_node, prev_i):
            # (closest txer strictly behind this node)
            lo_tx_i = prev_i
            while (prev_i + 1 < len_txers):
                if (this_node.in_hi_range_of(tx_sorted[prev_i + 1].x)):
                    lo_tx_i = prev_i + 1
                prev_i += 1
            return lo_tx_i

        def _find_lo_i(this_node, prev_i):
            # (furthest node within range behind this one)
            lo_i = prev_i
            while (prev_i + 1 < len_all):
                if (this_node.in_hi_range_of(all_sorted[prev_i + 1].x)) and\
                   not (this_node.in_hi_range_of(all_sorted[prev_i].x)):
                    lo_i = prev_i + 1
                    break
                prev_i += 1
            return lo_i

        def _find_hi_i(this_node, prev_i):
            # (furthest node within range ahead of this one)
            hi_i = prev_i
            while (prev_i + 1 < len_all):
                if (this_node.in_lo_range_of(all_sorted[prev_i].x)) and\
                   not (this_node.in_lo_range_of(all_sorted[prev_i + 1].x)):
                    hi_i = prev_i
                    break
                prev_i += 1
            return hi_i

        prev_lo_tx_i = 0
        prev_lo_i = 0
        prev_hi_i = 0

        #Determine state of channel for each node
        for (this_i, this_node) in enumerate(all_sorted):

            lo_tx_i = _find_lo_tx_i(this_node, prev_lo_tx_i)
            lo_i = _find_lo_i(this_node, prev_lo_i)
            hi_i = _find_hi_i(this_node, prev_hi_i)

            idle_channel = True

            #Determine if tx'er nodes are in range
            #Delivers message piece if single txer in range
            if  (lo_tx_i + 1 < len_txers) and\
                (this_node.in_range_of(tx_sorted[lo_tx_i + 1].x)):

                idle_channel = False

                if not (this_node.in_range_of(tx_sorted[lo_tx_i].x)):

                    this_node.receive_message_from(tx_sorted[lo_tx_i + 1])

            elif (lo_tx_i < len_txers) and\
                 (this_node.in_range_of(tx_sorted[lo_tx_i].x)):

                idle_channel = False

                this_node.receive_message_from(tx_sorted[lo_tx_i])

            #Update the node's local channel conditions
            this_node.update_local_conditions(idle_channel, hi_i - lo_i)

            prev_lo_tx_i = lo_tx_i
            prev_lo_i = lo_i
            prev_hi_i = hi_i

    """
    Transitions all nodes in network to the assigned next state
        -Requires 'channel_is_idle' set for each node
    """
    def transition_sim(self):

        for node in self.all_nodes:

            node.transition_state()
