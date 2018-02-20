#from sim import SLOT_TIME, CW_NOMINAL, IFS_TIME, BEACON_PERIOD, PACKET_SIZE, SIM_LIMIT
import random
from config import *

class State:
    idle, sense, count, tx = ("idle", "sense", "count", "tx")

class CW_PRNG:
    def gen_CW(self):
        #FIXME - Double check that's correct
        val = random.uniform(0, CW_NOMINAL * 1.0 * SLOT_TIME)

        if not val:
            assert 0, "blep: {}".format(val)

        return val

class Message_Piece:
    def __init__(self, uuid, location, msg_uuid):
        self.origin_uuid = uuid
        self.location = location
        self.msg_uuid = msg_uuid
        self.is_start = True
        self.is_end = False
        self.seq_num = 0


class DSRC_Node:

    def __init__(self, uuid, init_x, init_v, clock):

        self.cs = State.idle
        self.ns = State.idle

        self.uuid = uuid
        self.sys_clock = clock

        # Road related vars
        self.x = init_x
        self.v = init_v
        self.finished = False

        #Local channel conditions
        self.channel_is_idle = False

        # Beaconing logic vars
        self.beacon_counter = 0 #init to 0 causes beacon generation immediately

        # "Sense" state vars
        self.ifs_cnt = IFS_TIME

        # "Count" state vars
        self.cw_cnt = 0
        self.generator = CW_PRNG()
        self._gen_new_CW()

        # "Tx" state vars
        self.tx_cnt = PACKET_SIZE
        self.packet_id = 0
        self.message = None

        # Receiver band vars
        self.tx_origin = None
        self.tx_msg_id = None
        self.tx_seq = None

        ##############################
        # "Extra" vars for statistics
        ##############################
        self.packet_cnt = 0
        self.finished_tx_cnt = 0
        self.expired_cnt = 0
        self.longest_delay = 0
        self.packet_creation_time = 0 #Set when new beacon is generated
        self.aggr_delay_time = 0

        # Log 'ack's from rx'ers here
        self.start_rx_set = set()
        self.end_rx_set = set()

    ###########################################################################
    # Public Class Methods
    ###########################################################################

    """
    Step the node through the DSRC FSM according to current state
    Returns: A string summarizing a finished message or empty string
    """
    def step_state(self):

        ret = ""

        #######################################
        # Step through the DSRC Beaconing FSM #
        #######################################
        if (self.cs is State.tx):
            #Blindly tx another packet piece, regardles of network conditions
            self.tx_cnt -= self.sys_clock.dt * TX_RATE

            if (self.tx_cnt <= 0):
                #Transmission finished
                ret = self._log_finished_tx()

                #Move to idle
                self.ns = State.idle

        elif (self.channel_is_idle):

            if (self.cs is State.sense):
                self.ifs_cnt -= self.sys_clock.dt

                if (self.ifs_cnt <= 0):
                    #Channel determined Idle
                    self.ns = State.count

            elif (self.cs is State.count):
                self.cw_cnt -= self.sys_clock.dt

                if (self.cw_cnt <= 0):
                    #Free to begin transmitting
                    self.ns = State.tx

        else: #Channel is busy, reset values
            if (self.cs is State.sense):
                self.ifs_cnt = IFS_TIME
            elif (self.cs is State.count):
                self.ns = State.sense

        ###############################
        # Periodic Beacon generation  #
        ###############################
        self.beacon_counter -= self.sys_clock.dt

        if (self.beacon_counter <= 0):
            #Beacon period has elapsed. Generate new beacon
            self.beacon_counter = BEACON_PERIOD
            self.packet_cnt += 1
            self.packet_creation_time = self.sys_clock.time

            if not (self.ns is State.idle):
                #Hadn't tx'd last packet!
                self.expired_cnt += 1
                #Immediate transition to idle
                self.cs = State.idle

            self.ns = State.sense

        ######################################
        # Variable cleanup for state changes #
        ######################################
        if (self.cs != self.ns):
            self._cleanup_state_transition()

        return ret

    """
    Step the node in simulated space
        -Nodes determined 'finished' once they drive full length of road
        -Returns True when a node finishes, False otherwise
    """
    def step_traffic_sim(self):

        x = self.x + (self.sys_clock.dt * self.v)
        self.x = x

        if (x >= ROAD_LIMIT):
            self.finished = True

        return self.finished

    """
    Creates the message this node will advertise over the next step
    """
    def update_message(self):

        if (self.message is not None):
            self.message.seq_num += 1
            self.message.location = self.x
            self.message.is_start = False
            if self.tx_cnt - (self.sys_clock.dt * TX_RATE) <= 0:
                #This is the last piece to tx
                self.message.is_end = True

        else:
            #Create a new packet/message iterator
            self.message = Message_Piece(self.uuid, self.x, self.packet_id)
            self.packet_id += 1
    """
    Log the message transmitted from provided node
    Might perform logging internal to the tx_node
    Returns: None
    """
    def delivery_from(self, tx_node):

        assert tx_node.message is not None

        tx_uuid = tx_node.message.origin_uuid
        tx_loc = tx_node.message.location
        msg_uuid = tx_node.message.msg_uuid
        this_seq = tx_node.message.seq_num

        if (tx_node.message.is_start):
            #Resets any previously held state...
            self.tx_origin = tx_uuid
            self.tx_msg_id = msg_uuid
            self.tx_seq = this_seq
            tx_node._ack_start(self)

        elif ((tx_uuid != self.tx_origin) or
                (msg_uuid != self.tx_msg_id)):
            #Loss of continuity...
            self.tx_origin = None
            self.tx_msg_id = None
            self.tx_seq = 0

        elif (this_seq != self.tx_seq + 1):
            #Loss of continuity...
            self.tx_origin = None
            self.tx_msg_id = None
            self.tx_seq = 0

        else:
            #Continuation of current message
            self.tx_seq = this_seq

            if tx_node.message.is_end:

                #Completed Message!
                tx_node._ack_end(self)


    ###########################################################################
    # Private Class Methods
    ###########################################################################
    """
    Generate a new Contention Window value
    """
    def _gen_new_CW(self):

        val = self.generator.gen_CW()
        assert(val), "_gen_new_CW"
        self.cw_cnt = val


    """
    Node transitions state
        -State vars are cleaned up upon exit from corresponding state
    """
    def _cleanup_state_transition(self):

        if self.cs is State.idle:
            #The internal beaconing logic initiates idle->sense transition
            #Reset all state values. Deals with edge case caused by new beacon
            self.ifs_cnt = IFS_TIME
            self._gen_new_CW()
            self.tx_cnt = PACKET_SIZE
            self.message = None

        elif self.cs is State.sense:
            self.ifs_cnt = IFS_TIME

        elif self.cs is State.count:
            if self.ns is State.sense:
                pass #Case where CW value persists, no cleanup necessary
            else:
                self._gen_new_CW()

        elif self.cs is State.tx:
            self.tx_cnt = PACKET_SIZE
            self.message = None

        else:
            raise "ooops, '_do_state_transition'"

        self.cs = self.ns


    ###########################################################################
    # Magic
    ###########################################################################

    def _ack_start(self, rx_node):
        self.start_rx_set.add(rx_node)

    def _ack_end(self, rx_node):
        self.end_rx_set.add(rx_node)

    """
    Nodes keep statistics internally about delays between completed beacons
        -Longest individual Packet Interarrival time kept for worst case stats
        -Average interarrival time calculated at the end

    Returns: String summarizing the rx ack's for this message
    """
    def _log_finished_tx(self):

        ret = ""

        time_now = self.sys_clock.time
        this_tx_delay = time_now - self.packet_creation_time

        if (this_tx_delay > self.longest_delay):
            self.longest_delay = this_tx_delay

        self.finished_tx_cnt += 1
        self.aggr_delay_time += this_tx_delay

        if (self.sys_clock.time > 1) and\
            (self.x > TX_RANGE) and\
            (self.x < ROAD_LIMIT - TX_RANGE):

            rcvd = len(self.end_rx_set)
            tot = rcvd + len(self.start_rx_set)

            end_nodes = "".join(\
                "{},".format(node.uuid) for node in self.end_rx_set)
            dropped_nodes = "".join(\
                "{},".format(node.uuid) for node in (self.start_rx_set - self.end_rx_set))
            ret = "NODE#{:n}: PKT#{:n} x={:.2f} rate={}/{} | {} | {}\n".format(\
                self.uuid, self.packet_id, self.x,\
                rcvd, tot, end_nodes, dropped_nodes)

        return ret
