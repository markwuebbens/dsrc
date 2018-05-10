import random
import string
from config import SLOT_TIME, BEACON_PERIOD, PACKET_SIZE, IFS_TIME, TX_RATE
from logger import DSRC_Node_Logger

class State:
    idle, sense, count, tx = ("idle", "sense", "count", "tx")

class Beacon_PRNG:
    @staticmethod
    def gen_beacon():
        return random.uniform(0, BEACON_PERIOD)

class Name_Generator:
    @staticmethod
    def gen(uuid, chars = string.ascii_uppercase, size = 3):
        return ''.join(random.choice(chars) for _ in range(size)) +\
               '_{:n}'.format(uuid)

class Message_Piece:
    def __init__(self, uuid, msg_uuid, location):
        self.origin_uuid = uuid
        self.msg_uuid = msg_uuid
        self.location = location
        self.is_start = True
        self.is_end = False
        self.seq_num = 0

    def update(self, bits_left, dt):
        self.seq_num += 1
        self.is_start = False
        self.is_end = (bits_left <= dt * TX_RATE)



class DSRC_Node:

    def __init__(self, clock, log_dir,\
                 uuid, init_x, init_v,\
                 CW_Generator, TX_Range, Road_Limit):

        self.cs = State.idle

        self.uuid = uuid
        self.name = Name_Generator.gen(uuid)

        self.sysclock = clock

        self.logger = DSRC_Node_Logger(log_dir, str(uuid), clock.timenow())

        # Road related vars
        self.x = init_x
        self.v = init_v
        self.limit = Road_Limit
        self.is_finished = False

        # DSRC config parameters
        self.tx_range = TX_Range
        self.cw_generator = CW_Generator

        #Local channel conditions (updated by network before each step)
        self.channel_is_idle = False
        self.local_density = 0

        # Beaconing state vars
        self.beacon_counter = Beacon_PRNG.gen_beacon()
        self.packet_creation_time = 0 #Set whenever new beacon is generated

        # "Sense" state vars
        self.ifs_cnt = IFS_TIME

        # "Count" state vars
        self.cw_cnt = 0

        # "Tx" state vars
        self.tx_start_density = 0
        self.tx_end_density = 0
        self.bits_left = PACKET_SIZE
        self.packet_id = 0
        self.message = None


        # Receiver band vars
        self.tx_origin = None
        self.tx_msg_id = None
        self.tx_seq = None

        ##############################
        # "Extra" vars for statistics
        ##############################

        # RX logging/ack'ing vars
        self.end_rx_set = set()
        self.start_rx_set = set()



    ###########################################################################
    # Public Class Methods
    ###########################################################################


    """
    Update internal understanding of the world
    """
    def update_local_conditions(self, is_idle, density, tx_node):

        self.channel_is_idle = is_idle
        self.local_density = density

        if (tx_node):
            #"You've got mail"

            msg_piece = tx_node.get_message_piece()

            tx_uuid = msg_piece.origin_uuid
            tx_loc = msg_piece.location
            msg_uuid = msg_piece.msg_uuid
            this_seq = msg_piece.seq_num

            if (msg_piece.is_start):
                #Resets any previously held state...
                self.tx_origin = tx_uuid
                self.tx_msg_id = msg_uuid
                self.tx_seq = this_seq
                tx_node.ack_start_msg(self)

            elif (tx_uuid != self.tx_origin) or\
                 (msg_uuid != self.tx_msg_id) or\
                 (this_seq != self.tx_seq + 1):
                #Loss of continuity...
                self.tx_origin = None
                self.tx_msg_id = None
                self.tx_seq = 0

            else:
                #Continuation of current message
                self.tx_seq = this_seq

                if msg_piece.is_end:
                    #Completed Message!
                    tx_node.ack_end_msg(self)

    """
    Execute relevant actions for this time step
        -Nodes step through a DSRC beaconing FSM
        -State specific actions executed here

    """
    def step(self):

        ############################
        # Execute actions by state #
        ############################
        if (self.cs is State.tx):

            assert self.message is not None, "oops, step (tx_state message)"
            self.bits_left -= self.sysclock.stepsize() * TX_RATE

            #FIXME - hacky logging...
            if (message.is_start):
                self.tx_start_density = self.local_density
            if (message.is_end):
                self.tx_end_density = self.local_density

        elif (self.cs is State.sense):
            self.ifs_cnt -= self.sysclock.stepsize()

        elif (self.cs is State.count):
            self.cw_cnt -= self.sysclock.stepsize()

        elif (self.cs is State.idle):
            pass

        else:
            assert 0, "Whoops, step"

        ###############################
        # Periodic Beacon MSG counter #
        ###############################
        self.beacon_counter -= self.sysclock.stepsize()

        ##############################################
        # Step the node in simulated space           #
        # Labeled as 'finished' once past ROAD_LIMIT #
        ##############################################
        self.x = self.x + (self.sysclock.stepsize() * self.v)
        self.is_finished = (self.x > self.limit)

        return self.is_finished


    """
    Transition cs->ns as applicable
    REQUIRES - current 'channel_is_idle' value
    OUTPUT - 'message' piece if txing
    RETURN - (self.cs == State.tx) - boolean indicating the node is now tx'ing
    """
    def transition_state(self):

        new_state = None

        #Check for transition conditions on a per-state basis
        if self.cs is State.tx:
            if (self.bits_left <= 0):
                #Just finished TX'ing a packet
                self._log_finished_tx()
                new_state = State.idle
            else:
                #Update the message object
                self.message.update(self.bits_left, self.sysclock.stepsize())


        elif self.cs is State.sense:
            if not self.channel_is_idle:
                #Reset ifs state when not idle
                new_state = State.sense
            elif (self.ifs_cnt <= 0):
                #Interframe spacing period detected
                new_state = State.count

        elif self.cs is State.count:
            if not self.channel_is_idle:
                new_state = State.sense
            elif (self.cw_cnt <= 0):
                #CW window has elapsed, begin transmitting
                new_state = State.tx

        #Check for state transition caused by new beacon generation
        if (self.beacon_counter <= 0):
            #Beacon period has elapsed, reset counter
            self.beacon_counter = BEACON_PERIOD
            #Generate new beacon packet
            self.packet_creation_time = self.sysclock.timenow()
            self.packet_id += 1
            self.message = Message_Piece(self.uuid, self.packet_id, self.x)
            #Generate a random CW for this packet
            self._gen_new_CW()
            #Try to gain access to channel
            new_state = State.sense

        #Execute transition to new state
        if new_state is not None:
            if (new_state is State.sense):
                self.ifs_cnt = IFS_TIME

            elif (new_state is State.tx):

                self.tx_start_density = self.local_density

                self.start_rx_set.clear()
                self.end_rx_set.clear()

                self.bits_left = PACKET_SIZE

            self.cs = new_state

        return (self.cs is State.tx)

    """
    Returns this node's message piece for the interval
    """
    def get_message_piece(self):
        return self.message

    def ack_start_msg(self, rx_node):
        self.start_rx_set.add(rx_node)

    def ack_end_msg(self, rx_node):
        self.end_rx_set.add(rx_node)

    def in_hi_range_of(self, other_x):
        return (other_x < self.x) and (other_x + self.tx_range >= self.x)

    def in_lo_range_of(self, other_x):.
        return (other_x >= self.x) and (self.x + self.tx_range >= other_x)

    def in_range_of(self, other_x):
        return self.in_hi_range_of(other_x) or\
               self.in_lo_range_of(other_x)

    ###########################################################################
    # Private Class Methods
    ###########################################################################
    """
    Generate a new Contention Window value
    """
    def _gen_new_CW(self):


        val = self.cw_generator.gen()
        assert(val), "_gen_new_CW"
        self.cw_cnt = val



    ###########################################################################
    # Logging Magic
    ###########################################################################

    """
    Log stats about the finished message to disk
    """
    def _log_finished_tx(self):

        if (self.sysclock.timenow() > 0.3) and\
            (self.x > self.tx_range) and\
            (self.x < self.limit - self.tx_range):

            start_set_sz = len(self.start_rx_set)
            start_set_str = "".join(\
                "{:n} ".format(node.uuid) for node in self.start_rx_set)

            end_set_sz = len(self.end_rx_set)
            end_set_str = "".join(\
                "{:n} ".format(node.uuid) for node in self.end_rx_set)

            self.logger.log_packet(self.packet_id, self.x,\
                                   self.packet_creation_time,\
                                   self.sysclock.timenow(),\
                                   self.tx_start_density, self.tx_end_density,\
                                   start_set_sz, start_set_str,\
                                   end_set_sz, end_set_str)

