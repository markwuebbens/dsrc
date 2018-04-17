import os
import math
import random

from node import State, DSRC_Node

class DSRC_Network:

    def __init__(self, clock, log_dir,\
                 Avg_Speed, Speed_Delta, Avg_Density,\
                 CW_Generator, TX_Range, Road_Limit):

        self.sysclock = clock
        self.log_dir = log_dir

        #Config vars for the network
        self.Avg_Speed = Avg_Speed
        self.Speed_Delta = Speed_Delta
        self.Avg_Density = Avg_Density

        #Config vars passed to the nodes
        self.CW_Generator = CW_Generator
        self.TX_Range = TX_Range
        self.Road_Limit = Road_Limit

        #Total num nodes simulated in the network
        self.total_cnt = 0

        self.next_node_id = 0

        #Set of ALL nodes in simulation
        self.all_nodes = set()

        #List of nodes which are tx'ing
        self.tx_nodes = set()

        #Fill the length of the road with vehicles
        marker = Road_Limit;
        while (marker > 0):

            self._generate_node(marker)
            marker -= self.sysclock.stepsize() * self.Avg_Speed


    ###########################################################################
    # Private Class Methods
    ###########################################################################
    """
    Add a node to the network with probability 'density_weight'
    """
    def _generate_node(self, init_x = 0):

        coin_toss = random.random()

        density_weight = self.sysclock.stepsize() * self.Avg_Speed * self.Avg_Density #s * m/s * veh/m

        if (coin_toss < density_weight):

            velocity = random.uniform(self.Avg_Speed - self.Speed_Delta,\
                                      self.Avg_Speed + self.Speed_Delta)

            node = DSRC_Node(self.sysclock, self.log_dir,\
                            self.next_node_id, init_x, velocity,\
                            self.CW_Generator, self.TX_Range, self.Road_Limit)

            self.next_node_id += 1
            self.all_nodes.add(node)
            self.total_cnt += 1

    """
    Perform one step of the top level traffic simulation
        -Each node in the network executes their state independently
        -Nodes increment in space and time, updating counters and state
        -Nodes that pass the road limit are marked as 'finished' and returned
    """
    def _step_logical(self):

        finished_nodes = set()
        self.tx_nodes = set()

        self._generate_node()

        for node in self.all_nodes:

            node.step_logical()

            #Aggregate 'finished' nodes
            if (node.is_finished):
                finished_nodes.add(node)

            #Aggregate nodes which are tx'ing right now
            elif (node.cs is State.tx):
                self.tx_nodes.add(node)

        return finished_nodes

    """
    Network informs each node of any valid transmissions and of local channel conditions
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
    def _transition_sim(self, finished_nodes):

        #Remove finished nodes from the network
        self.all_nodes = self.all_nodes - finished_nodes

        #Everyone else transitions to the next state
        for node in self.all_nodes:

            node.transition_state()

    ###########################################################################
    # Public Class Methods
    ###########################################################################
    """
    Each node steps forward logically and independently
    Channel conditions are determined for the entire network
    Each node transitions according to local conditions
    """
    def step(self):

        # -Each node: Moves forward logically in time and space
        # -'Finished' nodes are returned
        finished_nodes = self._step_logical()


        #Network arbitrates message tx'ing and collision for curr state
        # -First sorts tx_nodes and all_nodes lists
        # -Each node: Receives a valid transmission
        #             Receives it's current local channel state
        # @REQUIRES - network._step_logical() has been called!
        self._arbitrate_channel_conditions()


        #Network elements increment logically in time and space
        # -'Finished' nodes are removed from the network
        # -Each node: Executes (cs -> ns) in the DSRC FSM according to local
        #   conditions
        # @REQUIRES - network.arbitrate_channel_conditions() has been called!
        self._transition_sim(finished_nodes)

        return finished_nodes




