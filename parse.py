import sys

sum_dict = {}
count_dict = {}

rate_total = 0.0
msg_total = 0

Sum_Cnt_By_Rho_dict = {}

def scrape_node(filename):


    global Sum_Cnt_By_Rho_dict

    node_num = filename.split('/')[1].split('_')[0]

    print 'ello from {}'.format(node_num)

    with open(filename, 'r') as file:


        for line in file:

            toks = line[:-1].split("|")

            if len(toks) < 5:
                continue

            try:

                [packet_id, location]        = toks[0].split('@')
                [start_time, end_time]       = toks[1].split(' ')
                [start_density_str, end_density_str] = toks[2].split(' ')
                [start_cnt, start_list]      = toks[3].split('-')
                [end_cnt, end_list]          = toks[4].split('-')

                start_nodes                  = start_list[:-1].split(' ')
                start_density = int(start_density_str) + 1
                end_nodes                    = end_list[:-1].split(' ')
                end_density = int(end_density_str) + 1

            except Exception as e:
                print 'fuck ->', line
                print e.message
                print e.args
                sys.exit

            else:

                if start_density in Sum_Cnt_By_Rho_dict:
                    (sum_now, cnt_now) = Sum_Cnt_By_Rho_dict[start_density]

                    Sum_Cnt_By_Rho_dict[start_density] = (sum_now + len(end_nodes)*1.0/start_density, cnt_now + 1)

                else:
                    Sum_Cnt_By_Rho_dict[start_density] = (len(end_nodes)*1.0/start_density, 1)






scrape_node(sys.argv[1])
scrape_node(sys.argv[2])
scrape_node(sys.argv[3])
scrape_node(sys.argv[4])
scrape_node(sys.argv[5])

for rho in Sum_Cnt_By_Rho_dict:

    (this_sum, this_cnt) = Sum_Cnt_By_Rho_dict[rho]

    print 'Density {} (sz {}) has avg_rate = {}'.format(rho, this_cnt, this_sum/this_cnt)

#with open(sys.argv[1], 'r') as raw:
#
#    time = ""
#
#    for line in raw:
#        toks = line.split(" ")
#
#        if ((len(toks) > 2) and (toks[1] == "HELLO.")): break
#
#        elif (len(toks) == 2):
#            time = toks[1][0:-2]
#
#        elif (len(toks) > 3):
#
#            start = ""
#            start_len = 0
#            end = ""
#            end_len = 0
#
#            uuid = int(toks[0][0:-1])
#            msg_id = int(toks[1][3:])
#            x = toks[2][2:]
#
#            nodes = line.split(" | ")[1].split(" ")
#            assert len(nodes) == 2
#
#            if (len(nodes[0]) > 1):
#                end = nodes[0][:-1]
#                end_len = len(end.split(","))
#
#            if (len(nodes[1]) > 3):
#                start = nodes[1][1:-3]
#                start_len = len(start.split(","))
#
#            #print "|{}|{}|   |{}|{}|".format(end, end_len, start, start_len)
#            if (start_len + end_len > 0):
#                rcvd_rate = (end_len * 1.0) / (end_len+start_len)
#
#                rate_total += rcvd_rate
#                msg_total += 1
#
#                if (uuid in sum_dict):
#                    sum_dict[uuid] += rcvd_rate
#                    count_dict[uuid] += 1
#
#                else:
#                    sum_dict[uuid] = rcvd_rate
#                    count_dict[uuid] = 1
#
#
#
#            #out.write("{}, {}, {}, {}, {}\n".format(time, uuid, msg_id, x, rcvd_rate))
#
#
#
##Now begin calculating sample standard deviations
#sig_sum_total = 0.0
#sig_count = 0
#
##Calculte avg success rate of all messages sent
#overall_avg = rate_total/msg_total
#
##Calculate std devs per node as well
#sig_sum_dict = {}
#sig_count_dict = {}
#
##Calculate avg success rate for each node
#avg_rates_dict = {}
#for uuid in sum_dict:
#    avg_rates_dict[uuid] = sum_dict[uuid] / count_dict[uuid]
#
#assert len(avg_rates_dict) == len(count_dict)
#
#with open(sys.argv[1], 'r') as raw:
#
#    time = ""
#
#    for line in raw:
#        toks = line.split(" ")
#
#        if ((len(toks) > 2) and (toks[1] == "HELLO.")): break
#
#        elif (len(toks) == 2):
#            time = toks[1][0:-2]
#
#        elif (len(toks) > 3):
#
#            start = ""
#            start_len = 0
#            end = ""
#            end_len = 0
#
#            uuid = int(toks[0][5:-1])
#            msg_id = int(toks[1][3:])
#            x = toks[2][2:]
#
#            all_nodes = line.split(" | ")
#            assert len(all_nodes) == 3
#
#            end_nodes = all_nodes[1].split(",")
#            drop_nodes = all_nodes[2].split(",")
#
#            #JUST PRINT PLZ
#
#            if (len(nodes[0]) > 1):
#                end = nodes[0][:-1]
#                end_len = len(end.split(","))
#
#            if (len(nodes[1]) > 3):
#                start = nodes[1][1:-3]
#                start_len = len(start.split(","))
#
#            #print "|{}|{}|   |{}|{}|".format(end, end_len, start, start_len)
#
#
#            if (start_len + end_len):
#                rcvd_rate = (end_len * 1.0) / (end_len+start_len)
#
#                sig_sum_total += (rcvd_rate - overall_avg)**2
#                sig_count += 1
#
#                if (uuid in sig_sum_dict):
#                    sig_sum_dict[uuid] += (rcvd_rate - avg_rates_dict[uuid])**2
#                    sig_count_dict[uuid] += 1
#
#                else:
#                    sig_sum_dict[uuid] = (rcvd_rate - avg_rates_dict[uuid])**2
#                    sig_count_dict[uuid] = 1
#
#
#assert sig_count == msg_total
#
#
#with open(sys.argv[2], 'w') as out:
#    out.write("AVG RATE IS: {:.4f} SD {:.4f} ({:n} msgs)\n\n".format(\
#        overall_avg, sig_sum_total / sig_count, sig_count))
#
#    out.write("BY NODE:\n")
#    for uuid in sum_dict:
#
#        assert sig_count_dict[uuid] == count_dict[uuid]
#
#        out.write("{:n} - {:.4f} SD {:.4f} ({:n})\n".format(\
#            uuid, avg_rates_dict[uuid],\
#            sig_sum_dict[uuid] / sig_count_dict[uuid],\
#            count_dict[uuid]))
#
#        """
#        print end, "|", start, "|", start.split(",")
#        print end.split(','), " | ", start.split(',')
#        rcvd = len(end.split(','))
#
#        """
#
#
#
#
#
#
