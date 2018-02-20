class Header_Ln:
    @staticmethod
    def to_str(uuid, time):
        return "LOGGING {:n} TIMENOW: {:.4f}\n".format(uuid, time)

class Packet_Ln:
    @staticmethod
    def to_str(pkt_id, node_x, gen_time, end_time,
                start_count, end_count, #num cars in vicinity at start + end
                start_rx_str, end_rx_str):

        return "{:n},{:.3f}|{:.5f},{:.5f}|{:n}-{} |{:n}-{}\n".format(\
            pkt_id, node_x, gen_time, end_time,
            start_count, start_rx_str,
            end_count, end_rx_str)

class DSRC_Packet_Logger:
    def __init__(self, filename, node_uuid, time_now):
        self.uuid = uuid;
        self.filename = filename;
        self.write_line(Header_Ln().to_str(node_uuid, time_now))

    def write_line(self, line):
        with open(self.filename, 'a+') as out:
            out.write(line)

    def log_packet(packet_id, node_x
                    gen_time, end_time,
                    start_count, end_count, #num cars in vicinity at start + end
                    start_rx_str, end_rx_str):

        self.write_line(Packet_Ln().to_str(\
                packet_id, node_x,
                gen_time, end_time,
                start_count, end_count,
                start_rx_str, end_rx_str))




class DSRC_Log_Parser:
    def __init__(self, filename):
        self.filename = filename

