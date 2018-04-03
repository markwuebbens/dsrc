import sys
import os

Road_Limit = 500 #m
TX_Range = None
Sum_Cnt_By_Rho_dict = {}

def scrape_node(directory, filename):


    global Sum_Cnt_By_Rho_dict
    global Road_Limit
    global TX_Range

    node_num = filename.split('_')[0]

    #print 'ello from {}'.format(node_num)

    with open(directory + filename, 'r') as file:


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
                this_density = int(start_density_str) + 1
                end_nodes                    = end_list[:-1].split(' ')
                end_density = int(end_density_str) + 1

            except Exception as e:
                print e.message
                print e.args
                sys.exit

            else:

                x_coord = float(location[:-1])
                if (x_coord > (Road_Limit - (TX_Range * 2))) or\
                   (x_coord < (TX_Range * 2)):
                    continue

                if this_density == 0:
                    print "Weirdness: '{}'".format(line)
                    print "node_num={}, loc={}, start_str='{}', end_str='{}'".format(node_num, location, toks[3], toks[4])
                    print x_coord
                    continue

                elif this_density in Sum_Cnt_By_Rho_dict:

                    (sum_now, cnt_now) = Sum_Cnt_By_Rho_dict[this_density]

                    Sum_Cnt_By_Rho_dict[this_density] = (sum_now + len(end_nodes), cnt_now + 1)

                else:

                    Sum_Cnt_By_Rho_dict[this_density] = (len(end_nodes), 1)

def scrape_directory(directory):

    toks = directory[:-1].split('_')
    global TX_Range

    try:
        max_cw   = toks[-1][:-1] #s
        rho      = toks[-2][:-3] #vpn
        avg_vel  = toks[-3][:-3] #mps
        tx_range = toks[-4][:-1] #m

        TX_Range = float(tx_range)

    except Exception as e:
        print e.message
        print e.args
        sys.exit

    else:
        for filename in os.listdir(directory):
            if filename.endswith('.log'):
                scrape_node(directory, filename)

def print_final_stats():

    print '{},{},{}'.format('rho', 'sz', 'rate')
    for rho in Sum_Cnt_By_Rho_dict:

        (this_sum, this_cnt) = Sum_Cnt_By_Rho_dict[rho]

        if (rho*this_cnt <= 0):
            print "FIXME!: rho={}, samples={}".format(rho, this_cnt)
            continue

        avg_rate = (this_sum*1.0)/(rho*this_cnt)

    
        print '{},{},{}'.format(rho, this_cnt, avg_rate)



scrape_directory(sys.argv[1])
print_final_stats()

