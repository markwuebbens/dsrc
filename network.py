import os
import math
import random

from node import State, DSRC_Node

class DSRC_Network:

    def __init__(self, clock, log_dir,\
                 Avg_Speed, Speed_Delta, Avg_Density,\
                 CW_Generator, TX_Range):

        self.sysclock = clock
        self.log_dir = log_dir

        #Config vars for the network
        self.Avg_Speed = Avg_Speed
        self.Speed_Delta = Speed_Delta
        self.Avg_Density = Avg_Density

        #Config vars passed to the nodes
        self.CW_Generator = CW_Generator
        self.TX_Range = TX_Range

        #Total num nodes simulated in the network
        self.total_cnt = 0

        self.next_node_id = 0

        #Set of ALL nodes in simulation
        self.all_nodes = set()

        #List of nodes which are tx'ing
        self.tx_nodes = set()


    ###########################################################################
    # Private Class Methods
    ###########################################################################

    """
    Network informs each node of any valid transmissions and of local channel conditions
    -INPUT - (self.tx_nodes) a list of the nodes in the network which are transmitting
           - (self.all_nodes) a list of all of the nodes in the network
    -OUTPUT - For every node in the network determine:
                -idle_channel: boolean indicating the channel is idle
                -local_density: number of other vehicles within tx range
                -valid_tx_node: a reference to a node which is tx'ing this step
                                -OR- None
    """
    def _arbitrate_channel_conditions(self):

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
            # (furthest node within range ahead of this one) (or this one)
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
            valid_txer = None

            #Determine if single valid tx'er node in range
            #Also determines if channel is idle
            if  (lo_tx_i + 1 < len_txers) and\
                (this_node.in_range_of(tx_sorted[lo_tx_i + 1].x)):

                idle_channel = False

                if not (this_node.in_range_of(tx_sorted[lo_tx_i].x)):

                    valid_txer = tx_sorted[lo_tx_i + 1]

            elif (lo_tx_i < len_txers) and\
                 (this_node.in_range_of(tx_sorted[lo_tx_i].x)):

                idle_channel = False

                valid_txer = tx_sorted[lo_tx_i]

            #Update the node's local channel conditions
            this_node.update_local_conditions(idle_channel, hi_i - lo_i, valid_txer)

            prev_lo_tx_i = lo_tx_i
            prev_lo_i = lo_i
            prev_hi_i = hi_i


    """
    Perform one step of the top level traffic simulation
        -Each node in the network executes their state independently
        -Nodes increment in space and time, updating counters and state
        -Nodes that pass the road limit are marked as 'finished' and returned
        -Updates the list of txing nodes AFTER they step
    -REQUIRES: _arbitrate_channel_conditions has been called
    -OUTPUT - self.tx_nodes, the list of txing nodes
    -RETURN - (finished_nodes) a list of the nodes considered 'finished'
    """
    def _step_logical(self):

        #Reset outputs of this step
        finished_nodes = set()
        self.tx_nodes = set()

        for node in self.all_nodes:

            #All Nodes in the network step forward
            if (node.step()):
                #Aggregate 'finished' nodes
                finished_nodes.add(node)

            #Not finished nodes transition to the next state
            elif (node.transition_state()):
                #Aggregate nodes which are now txing
                self.tx_nodes.add(node)

        #Remove finished nodes from the network
        self.all_nodes = self.all_nodes - finished_nodes

        return finished_nodes

    ###########################################################################
    # Public Class Methods
    ###########################################################################
    """
    Add a node to the network with probability 'density_weight'
    """
    def generate_node(self, init_x = 0):

        coin_toss = random.random()

        #s * m/s * veh/m
        density_weight = self.sysclock.stepsize() * self.Avg_Speed * self.Avg_Density

        if (coin_toss < density_weight):

            velocity = random.uniform(self.Avg_Speed - self.Speed_Delta,\
                                      self.Avg_Speed + self.Speed_Delta)

            node = DSRC_Node(self.sysclock, self.log_dir,\
                            self.next_node_id, init_x, velocity,\
                            self.CW_Generator, self.TX_Range,\
                            self.Avg_Speed + self.Speed_Delta)

            self.next_node_id += 1
            self.all_nodes.add(node)
            self.total_cnt += 1

    """
    Channel conditions are determined for the entire network
    Each node steps forward logically and independently
    Each node transitions according to local conditions
    """
    def step(self):

        #Attempt to generate a new node
        self.generate_node()

        #Network arbitrates message tx'ing and collision for curr state
        # -First sorts tx_nodes and all_nodes lists
        # -Each node: Receives a valid transmission
        #             Receives it's current local channel state
        self._arbitrate_channel_conditions()

        #Network elements increment logically in time and space
        # @REQUIRES - network._arbitrate_channel_conditions() has been called!
        # -Each node: Moves forward logically in time and space
        # -Each node: Executes (cs -> ns) in the DSRC beaconing FSM
        # -'Finished' nodes are removed from the network and returned
        return self._step_logical()




