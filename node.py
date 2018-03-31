import random
import string
from config import SLOT_TIME, BEACON_PERIOD, PACKET_SIZE, IFS_TIME, TX_RATE
from logger import DSRC_Node_Logger

class State:
    idle, sense, count, tx = ("idle", "sense", "count", "tx")

class Beacon_PRNG:
    @staticmethod
    def gen_beacon():
        val = random.uniform(0, BEACON_PERIOD)
        assert val, "Beacon_PRNG {}".format(val)
        return val


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

    def update(self, bit_cnt):
        self.seq_num += 1
        self.is_start = False
        self.is_end = (bit_cnt <= 0)


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

        # DSRC config specific values
        self.tx_range = TX_Range
        self.cw_generator = CW_Generator

        #Local channel conditions (updated by network each step)
        self.channel_is_idle = False
        self.local_density = 0

        # Beaconing state vars
        self.beacon_counter = Beacon_PRNG.gen_beacon()

        # "Sense" state vars
        self.ifs_cnt = IFS_TIME

        # "Count" state vars
        self.cw_cnt = 0
        self._gen_new_CW()

        # "Tx" state vars
        self.bit_cnt = PACKET_SIZE
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
        self.packet_creation_time = 0 #Set when new beacon is generated
        self.end_rx_set = set()
        self.start_rx_set = set()

        self.tx_start_density = 0


    ###########################################################################
    # Public Class Methods
    ###########################################################################

    """
    Execute relevant actions for this time step
        -Nodes step through a DSRC beaconing FSM
        -State specific actions executed here
    """
    def step_logical(self):

        ############################
        # Execute actions by state #
        ############################
        if (self.cs is State.tx):
            self._step_tx_state()

        elif (self.cs is State.sense):
            self._step_sense_state()

        elif (self.cs is State.count):
            self._step_count_state()

        elif (self.cs is State.idle):
            pass

        else:
            assert 0, "Whoops, step_logical"

        ##############################
        # Periodic Beacon generation #
        ##############################
        self._step_beacon()

        #############################################
        # Step the node in simulated space          #
        #    -Nodes 'finished' once past ROAD_LIMIT #
        #############################################
        self._step_traffic()

    """
    Transition cs->ns if applicable
        -requires current 'channel_is_idle' value
    """
    def transition_state(self):

        new_state = None
        if self.cs is State.tx:
            if (self.bit_cnt <= 0):
                new_state = State.idle

        elif self.cs is State.sense:
            if (self.channel_is_idle):
                if (self.ifs_cnt <= 0):
                    new_state = State.count
            else:
                new_state = State.sense

        elif self.cs is State.count:
            if (self.channel_is_idle):
                if (self.cw_cnt <= 0):
                    new_state = State.tx
                    #FIXME
                    self.tx_start_density = self.local_density
            else:
                new_state = State.sense

        if (self.beacon_counter <= 0):
            #Beacon period has elapsed. Generate new beacon
            self.beacon_counter = BEACON_PERIOD
            self.packet_creation_time = self.sysclock.timenow()
            new_state = State.sense

        if new_state != None:
            self._execute_transition(new_state)


    """
    Update internal understanding of the world
    """
    def update_local_conditions(self, is_idle, density):

        self.channel_is_idle = is_idle
        self.local_density = density


    """
    Receive the message piece transmitted from provided node
    """
    def receive_message_from(self, tx_node):

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

            if tx_node.message.is_end:
                #Completed Message!
                tx_node._ack_end(self)

    def in_hi_range_of(self, other_x):
        return (other_x < self.x) and (other_x + self.tx_range >= self.x)


    def in_lo_range_of(self, other_x):
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

    """
    Clears this node's message
    """
    def _clear_message(self):
        self.message = None

    """
    Execute steps for transmitting node
        -Creates the message this node will advertise this next step
        -Decrements bit_cnt
    """
    def _step_tx_state(self):

        self.bit_cnt -= self.sysclock.stepsize() * TX_RATE

        if self.message is None:
            #First time here: generate new message object
            self.packet_id += 1
            self.message = Message_Piece(self.uuid, self.packet_id, self.x)

        else:
            #Update the message object
            self.message.update(self.bit_cnt)

    """
    Execute steps for sensing node
        -Decrements ifs_cnt
    """
    def _step_sense_state(self):

        self.ifs_cnt -= self.sysclock.stepsize()


    """
    Execute steps for counting node
        -Decrements cw_cnt
    """
    def _step_count_state(self):

        self.cw_cnt -= self.sysclock.stepsize()


    """
    Decrements beacon_counter
    """
    def _step_beacon(self):

        self.beacon_counter -= self.sysclock.stepsize()


    """
    Steps the vehicle in logical space
        -Sets is_finished if ROAD_LIMIT reached
    """
    def _step_traffic(self):

        self.x = self.x + (self.sysclock.stepsize() * self.v)

        self.is_finished = (self.x > self.limit)


    """
    Causes node to transition to "next_state" state
        -Cleans up state specific vars for state transitioned ~from~
    """
    def _execute_transition(self, next_state):
        #print "Node {} is transitioning".format(self.uuid)

        if self.cs is State.idle:
            #The internal beaconing logic initiates transition out of idle
            #Reset all state vars. Deals with expired beacon edge case
            self.ifs_cnt = IFS_TIME
            self._gen_new_CW()
            self.bit_cnt = PACKET_SIZE
            self.start_rx_set.clear()
            self.end_rx_set.clear()
            self._clear_message()

        elif self.cs is State.sense:
            self.ifs_cnt = IFS_TIME

        elif self.cs is State.count:
            if next_state is State.sense:
                pass #Case where CW value persists
            else:
                self._gen_new_CW()

        elif self.cs is State.tx:
            #Just finished TX'ing a packet
            self._log_finished_message()
            #(Cleanup after magical logging)
            self.bit_cnt = PACKET_SIZE
            self.start_rx_set.clear()
            self.end_rx_set.clear()
            self._clear_message()

        else:
            assert 0, "oops, _execute_transition"

        self.cs = next_state



    ###########################################################################
    # Logging Magic
    ###########################################################################

    def _ack_start(self, rx_node):
        self.start_rx_set.add(rx_node)

    def _ack_end(self, rx_node):
        self.end_rx_set.add(rx_node)

    """
    Log stats about the finished message to disk
    """
    def _log_finished_message(self):

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
                                   self.tx_start_density, self.local_density,\
                                   start_set_sz, start_set_str,\
                                   end_set_sz, end_set_str)

