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
        msg_log = ""
        self.tx_nodes = set()

        for node in self.all_nodes:

            #Step to next state in DSRC fsm
            msg_log += node.step_state()

            #Aggregate and update nodes which are now tx'ing
            if (node.cs is State.tx):
                node.update_message()
                self.tx_nodes.add(node)

            #Node proceeds logically within the traffic sim
            #Aggregate 'finished' nodes
            if node.step_traffic_sim(): finished_nodes.add(node)


        #Remove finished nodes from the network
        self.all_nodes = self.all_nodes - finished_nodes

        return (finished_nodes, msg_log)

    """
    Nodes check local channel conditions and receive valid transmissions

    RETURNS: an aggregate of successful packet transmissions
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

        """
        def _above_range(node, other):
            return (node.x < other.x) and (node.x + TX_RANGE >= other.x)
        """
        #This index variable walks through the sorted list of tx'ing nodes
        #index always points to the lowest relevant tx node to consider
        lo_tx_i = 0

        #Determine state of channel for each node
        for (this_i, this_node) in enumerate(all_sorted):

            #Update lo_tx_i (closest txer strictly behind this node)
            while (_below_range(this_node, tx_sorted[lo_tx_i])):

                if (lo_tx_i + 1 < len_txers) and
                   (_below_range(this_node, tx_sorted[lo_tx_i + 1])):

                    lo_tx_i += 1
                else:
                    break

            #Find lo_i and hi_i
            # (furthest nodes within range behind and ahead of this one)
            lo_i = this_i
            while (lo_i - 1 >= 0) and
                  (_in_range(this_node, all_sorted[lo_i - 1])):
                lo_i -= 1

            hi_i = this_i
            while (hi_i + 1 < len_all) and
                  (_in_range(this_node, all_sorted[hi_i + 1])):
                hi_i += 1

            #Determine if a valid tx'er node is in range
            # (Deliver the message piece to this_node if so)
            if (lo_tx_i + 1 < len_txers) and
               (_in_range(this_node, tx_sorted[lo_tx_i + 1]) and
               (not _in_range(this_node, tx_sorted[lo_tx_i])):

                this_node.delivery_from(tx_sorted[lo_tx_i + 1])

            elif (_in_range(tx_sorted[lo_tx_i])):

                this_node.delivery_from(tx_sorted[lo_tx_i])

            #Update this_node's internal understanding of the world
            if (lo_tx_node is not None and _in_range(node, lo_tx_node)):
                node.channel_is_idle = False

            elif (hi_tx_node is not None and _in_range(node, hi_tx_node)):
                node.channel_is_idle = False

            else:
                node.channel_is_idle = True

            #Move index up to new lowest tx'er
            index = lo_tx

        #FIXME - here
        return message_aggr


    """
    Computes transmission statistics for each node in the simulation
    Prints some useful stuffs
    """
"""
    #**** HERE *****
    def compute_and_display_final_stats(self):

        longest_pir = 0
        lowest_avg = 1.0
        highest_avg = 0

        success_rate_agg = 0
        cnt = 0

        for node in self.all_nodes:

            #************* HERE **************
            # Do something clever
            if node.x > 100:

                cnt += 1.0

                success_rate = (1.0 * node.success_cnt) / node.packet_cnt

                if (not success_rate):
                    print "WHOOPS - This node didn't transmit anything..."

                    print "success | collision | total"
                    print "{}\t{}\t{}".format(\
                        node.success_cnt, node.collision_cnt, node.packet_cnt)
                success_rate_agg += success_rate

                if (node.longest_streak > longest_pir):
                    longest_pir = node.longest_streak

                if (success_rate < lowest_avg):
                    lowest_avg = success_rate

                if (success_rate > highest_avg):
                    highest_avg = success_rate

        assert cnt, "There were no valid nodes in the sim??"
        avg_success_rate = success_rate_agg / cnt

        print "\n-----> NETWORK STATISTICS ({} nodes)<-----".format(cnt)
        print "worst success rate: {} -- "\
              "best success rate: {} -- "\
              "Avg success rate: {}".format(\
              lowest_avg, highest_avg, avg_success_rate)
        print "longest PIR = {} sec".format(longest_pir)
"""
