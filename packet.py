class Header_Ln:
    @staticmethod
    def to_str(uuid, time):
        return "LOGGING NODE{:n} TIMENOW: {:.4f}\n".format(uuid, time)

class Packet_Ln:
    @staticmethod
    def to_str(pkt_id, node_x, gen_time, end_time,
                start_density, end_density, rcvd_str):

        return "{:n} {:.3f}|{:.5f} {:.5f}|{:n} {:n}|{}\n".format(\
            pkt_id, node_x, gen_time, end_time,
            start_density, end_density, end_rx_str)

class DSRC_Logger:
    def __init__(self, log_dir, uuid, time_now):
        self.filename = log_dir + "n" + str(uuid) + ".log";
        self.write_line(Header_Ln.to_str(uuid, time_now))

    def write_line(self, line):
        with open(self.filename, 'a+') as out:
            out.write(line)

    def log_packet(pkt_id, node_x
                    gen_time, end_time,
                    start_density, end_density,
                    rcvd_set_str):

        self.write_line(Packet_Ln.to_str(\
                pkt_id, node_x, gen_time, end_time,
                start_density, end_density,
                rcvd_set_str))




class DSRC_Log_Parser:
    def __init__(self, filename):
        self.filename = filename

