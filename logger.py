from config import PACKET_SIZE, TX_RATE

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

    def write_log(self, line):
        with open(self.path, 'w+') as log:
            log.write(line)

    def append_log(self, line):
        with open(self.path, 'a+') as log:
            log.write(line)

class DSRC_Node_Logger(DSRC_Logger):
    def __init__(self, log_dir, uuid_str, timenow):

        assert log_dir[-1] is '/'
        DSRC_Logger.__init__(self, log_dir, "node_{}.log".format(uuid_str, timenow))

        #self.write_log(Header_Ln.to_str(uuid, timenow))


    def log_packet(self, pkt_id, node_x,\
                    gen_time, end_time,\
                    start_density, end_density,\
                    start_sz, start_str,\
                    end_sz, end_str):

        self.append_log(Packet_Ln.to_str(\
                pkt_id, node_x, gen_time, end_time,\
                start_density, end_density,\
                start_sz, start_str,\
                end_sz, end_str))

class DSRC_Sim_Logger(DSRC_Logger):
    def __init__(self, stepsize, timenow, log_dir,\
                 Veh_Density, TX_Range, max_cw_time,
                 Avg_Speed, Speed_Delta, Road_Limit):

        assert log_dir[-1] is '/'

        #Create the log file which will store sim metadata
        DSRC_Logger.__init__(self, log_dir, "sim_settings.log")

        #Write the configured settings for this sim
        self.write_config(stepsize, timenow,\
                         Veh_Density, TX_Range, max_cw_time,\
                         Avg_Speed, Speed_Delta, Road_Limit)


    def write_config(self, steptime, timenow,\
                     Veh_Density, TX_Range, Max_CW_Time,\
                     Avg_Speed, Speed_Delta, Road_Limit):

        out =  "SETTINGS - {}\n".format(timenow)
        out += "TX_Range={}m\n".format(TX_Range)
        out += "Max CW delay={}s\n".format(Max_CW_Time)
        out += "Veh_Density={}veh/m\n".format(Veh_Density)
        out += "Speed is uniform over Avg_Speed(+-)DELTA_SPEED : {}+-{}m/s\n".format(Avg_Speed, Speed_Delta)
        out += "Road_Limit={}m\n".format(Road_Limit)
        out += "DT={}s\n".format(steptime)
        out += "PACKET_SZ={}b, TX_RATE={}b/s (tx_time={}s)\n".format(PACKET_SIZE, TX_RATE, PACKET_SIZE/TX_RATE)

        self.write_log(out)


    def write_summary(self, sim_time, num_finished, timenow):
        out  = "SUMMARY - {}\n".format(timenow)
        out += "{} nodes total simulated for {}s logically\n".format(num_finished, sim_time)

        self.append_log(out)

