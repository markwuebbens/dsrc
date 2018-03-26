from config import *

class Header_Ln:
    @staticmethod
    def to_str(uuid, time):
        return "LOGGING NODE{:n} TIMENOW: {:.4f}\n".format(uuid, time)

class Packet_Ln:
    @staticmethod
    def to_str(pkt_id, node_x, gen_time, end_time,\
               start_density, end_density,\
               start_sz, start_str, end_sz, end_str):

        return "{:n}@{:.3f}m|{:.6f} {:.6f}|{:n} {:n}|{:n}-{}|{:n}-{}\n".format(\
            pkt_id, node_x,\
            gen_time, end_time,\
            start_density, end_density,\
            start_sz, start_str, end_sz, end_str)

class DSRC_Logger:

    def __init__(self, log_dir, file_name):
        self.log_dir = log_dir
        self.filename = file_name
        self.path = log_dir + file_name

    def write_file(self, line):
        with open(self.path, 'w+') as out:
            out.write(line)

    def append_line(self, line):
        with open(self.path, 'a+') as out:
            out.write(line)

class DSRC_Node_Logger(DSRC_Logger):
    def __init__(self, log_dir, uuid, time_now):

        DSRC_Logger.__init__(self, log_dir, str(uuid) + "_node.log")

        self.write_file(Header_Ln.to_str(uuid, time_now))


    def log_packet(self, pkt_id, node_x,\
                    gen_time, end_time,\
                    start_density, end_density,\
                    start_sz, start_str,\
                    end_sz, end_str):

        self.append_line(Packet_Ln.to_str(\
                pkt_id, node_x, gen_time, end_time,\
                start_density, end_density,\
                start_sz, start_str,\
                end_sz, end_str))

class DSRC_Sim_Logger(DSRC_Logger):
    def __init__(self, log_dir):
        DSRC_Logger.__init__(self, log_dir, "sim_settings.log")

    def create_intro(self, clock, timenow):
        out  = "<--- HELLO. <{}>--->\n".format(timenow)
        out += "We are simulating a straight, uni-directional highway which is {} m long\n".format(ROAD_LIMIT)
        out += "The traffic density is set at {} veh/m\n".format(VEH_DENSITY)
        out += "Vehicles are traveling uniformly between {} and {} m/s\n".format(AVG_SPEED-SPEED_DELTA, AVG_SPEED+SPEED_DELTA)
        out += "The simulation runs at increments of {} s\n".format(clock.dt)
        out += "Vehicles are transmitting safety beacons over a {} m range\n".format(TX_RANGE)
        out += "msg len = {} bits, tx_rate = {} bps, time to tx = {} s\n".format(PACKET_SIZE, TX_RATE, PACKET_SIZE/TX_RATE)
        out += "The CW window is set to: 0 <= CW <= {} s\n".format(CW_NOMINAL*SLOT_TIME)
        return out

    def create_summary(self, clock, network, num_finished, timenow):
        out  = "<--- In Summary: --->\n"
        out += "Simulated {} nodes for a logical time of {} seconds\n".format(network.total_cnt, clock.time)
        out += "{} nodes drove past the limit of the sim\n".format(num_finished)
        out += "<--- GOODBYE. <{}>--->\n".format(timenow)
        return out

    def write_intro(self, clock, timenow):
        self.write_file(self.create_intro(clock, timenow))

    def write_summary(self, clock, network, num_finished, timenow):
        self.append_line(self.create_summary(clock, network, num_finished, timenow))

class DSRC_Log_Parser:
    def __init__(self, filename):
        self.filename = filename

