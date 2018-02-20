import sys

sum_dict = {}
count_dict = {}

rate_total = 0.0
msg_total = 0

with open(sys.argv[1], 'r') as raw:

    time = ""

    for line in raw:
        toks = line.split(" ")

        if ((len(toks) > 2) and (toks[1] == "HELLO.")): break

        elif (len(toks) == 2):
            time = toks[1][0:-2]

        elif (len(toks) > 3):

            start = ""
            start_len = 0
            end = ""
            end_len = 0

            uuid = int(toks[0][0:-1])
            msg_id = int(toks[1][3:])
            x = toks[2][2:]

            nodes = line.split(" | ")[1].split(" ")
            assert len(nodes) == 2

            if (len(nodes[0]) > 1):
                end = nodes[0][:-1]
                end_len = len(end.split(","))

            if (len(nodes[1]) > 3):
                start = nodes[1][1:-3]
                start_len = len(start.split(","))

            #print "|{}|{}|   |{}|{}|".format(end, end_len, start, start_len)
            if (start_len + end_len > 0):
                rcvd_rate = (end_len * 1.0) / (end_len+start_len)

                rate_total += rcvd_rate
                msg_total += 1

                if (uuid in sum_dict):
                    sum_dict[uuid] += rcvd_rate
                    count_dict[uuid] += 1

                else:
                    sum_dict[uuid] = rcvd_rate
                    count_dict[uuid] = 1



            #out.write("{}, {}, {}, {}, {}\n".format(time, uuid, msg_id, x, rcvd_rate))



#Now begin calculating sample standard deviations
sig_sum_total = 0.0
sig_count = 0

#Calculte avg success rate of all messages sent
overall_avg = rate_total/msg_total

#Calculate std devs per node as well
sig_sum_dict = {}
sig_count_dict = {}

#Calculate avg success rate for each node
avg_rates_dict = {}
for uuid in sum_dict:
    avg_rates_dict[uuid] = sum_dict[uuid] / count_dict[uuid]

assert len(avg_rates_dict) == len(count_dict)

with open(sys.argv[1], 'r') as raw:

    time = ""

    for line in raw:
        toks = line.split(" ")

        if ((len(toks) > 2) and (toks[1] == "HELLO.")): break

        elif (len(toks) == 2):
            time = toks[1][0:-2]

        elif (len(toks) > 3):

            start = ""
            start_len = 0
            end = ""
            end_len = 0

            uuid = int(toks[0][5:-1])
            msg_id = int(toks[1][3:])
            x = toks[2][2:]

            all_nodes = line.split(" | ")
            assert len(all_nodes) == 3

            end_nodes = all_nodes[1].split(",")
            drop_nodes = all_nodes[2].split(",")

            #JUST PRINT PLZ

            if (len(nodes[0]) > 1):
                end = nodes[0][:-1]
                end_len = len(end.split(","))

            if (len(nodes[1]) > 3):
                start = nodes[1][1:-3]
                start_len = len(start.split(","))

            #print "|{}|{}|   |{}|{}|".format(end, end_len, start, start_len)


            if (start_len + end_len):
                rcvd_rate = (end_len * 1.0) / (end_len+start_len)

                sig_sum_total += (rcvd_rate - overall_avg)**2
                sig_count += 1

                if (uuid in sig_sum_dict):
                    sig_sum_dict[uuid] += (rcvd_rate - avg_rates_dict[uuid])**2
                    sig_count_dict[uuid] += 1

                else:
                    sig_sum_dict[uuid] = (rcvd_rate - avg_rates_dict[uuid])**2
                    sig_count_dict[uuid] = 1


assert sig_count == msg_total


with open(sys.argv[2], 'w') as out:
    out.write("AVG RATE IS: {:.4f} SD {:.4f} ({:n} msgs)\n\n".format(\
        overall_avg, sig_sum_total / sig_count, sig_count))

    out.write("BY NODE:\n")
    for uuid in sum_dict:

        assert sig_count_dict[uuid] == count_dict[uuid]

        out.write("{:n} - {:.4f} SD {:.4f} ({:n})\n".format(\
            uuid, avg_rates_dict[uuid],\
            sig_sum_dict[uuid] / sig_count_dict[uuid],\
            count_dict[uuid]))

        """
        print end, "|", start, "|", start.split(",")
        print end.split(','), " | ", start.split(',')
        rcvd = len(end.split(','))

        """







