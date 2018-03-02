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
    Nodes receive valid transmissions and are informed of local channel conditions
    """
    def arbitrate_channel_conditions(self):

        tx_sorted = sorted(self.tx_nodes, key=lambda node: node.x)
        len_txers = len(tx_sorted)

        all_sorted = sorted(self.all_nodes, key=lambda node: node.x)
        len_all = len(all_sorted)

        #FIXME - probably put elsewhere
        def _in_range(node, other):
            return abs(node.x - other.x) <= TX_RANGE

        def _below_range(node, other):
            return (other.x < node.x) and (other.x + TX_RANGE >= node.x)

        #This index variable walks through the sorted list of tx'ing nodes
        #prev_lo_tx_i always points to the lowest relevant tx node to consider
        prev_lo_tx_i = 0

        #Determine state of channel for each node
        for (this_i, this_node) in enumerate(all_sorted):

            lo_tx_i = prev_lo_tx_i
            idle_channel = True
            lo_i = this_i
            hi_i = this_i

            #Update lo_tx_i (closest txer strictly behind this node)
            while (lo_tx_i < len_txers) and
                  (_below_range(this_node, tx_sorted[lo_tx_i])):

                if (lo_tx_i + 1 < len_txers) and
                   (_below_range(this_node, tx_sorted[lo_tx_i + 1])):

                    lo_tx_i += 1
                else:
                    break

            #Find lo_i and hi_i
            # (furthest nodes within range behind and ahead of this one)
            while (lo_i - 1 >= 0) and
                  (_in_range(this_node, all_sorted[lo_i - 1])):
                lo_i -= 1

            while (hi_i + 1 < len_all) and
                  (_in_range(this_node, all_sorted[hi_i + 1])):
                hi_i += 1

            #Determine if tx'er nodes are in range
            #Delivers message piece if single txer in range
            if (lo_tx_i + 1 < len_txers) and
               (_in_range(this_node, tx_sorted[lo_tx_i + 1])):

                idle_channel = False

                if (not _in_range(this_node, tx_sorted[lo_tx_i])):

                    this_node.receive_message_from(tx_sorted[lo_tx_i + 1])

            elif (lo_tx_i < len_txers) and
                 (_in_range(tx_sorted[lo_tx_i])):

                idle_channel = False

                this_node.receive_message_from(tx_sorted[lo_tx_i])

            #Update the_node's local channel conditions
            this_node.update_local_conditions(idle_channel, hi_i - lo_i)

            prev_lo_tx_i = lo_tx_i

    """
    Transitions all nodes in network to the assigned next state
        -Requires 'channel_is_idle' set for each node
    """
    def transition_sim(self):

        for node in self.all_nodes:

            if (node.cs != node.ns):

                node.transition_state()
