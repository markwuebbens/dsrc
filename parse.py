import sys
import os

from config import ROAD_LIMIT, TX_RANGE

Sum_Cnt_By_Rho_dict = {}

def scrape_node(filename):


    global Sum_Cnt_By_Rho_dict

    node_num = filename.split('_')[0]

    #print 'ello from {}'.format(node_num)

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
                this_density = int(start_density_str) + 1
                end_nodes                    = end_list[:-1].split(' ')
                end_density = int(end_density_str) + 1

            except Exception as e:
                print e.message
                print e.args
                sys.exit

            else:

                x_coord = float(location[:-1])
                if (x_coord > ROAD_LIMIT - (TX_RANGE * 1.5)) or\
                   (x_coord < TX_RANGE * 1.5):
                    continue

                if this_density in Sum_Cnt_By_Rho_dict:

                    (sum_now, cnt_now) = Sum_Cnt_By_Rho_dict[this_density]

                    Sum_Cnt_By_Rho_dict[this_density] = (sum_now + len(end_nodes), cnt_now + 1)

                else:

                    Sum_Cnt_By_Rho_dict[this_density] = (len(end_nodes), 1)

def scrape_directory(directory):

    for filename in os.listdir(directory):
        if filename.endswith('.log'):
            scrape_node(directory + filename)

def print_final_stats():

    print '{},{},{}'.format('rho', 'sz', 'rate')
    for rho in Sum_Cnt_By_Rho_dict:

        (this_sum, this_cnt) = Sum_Cnt_By_Rho_dict[rho]

        avg_rate = (this_sum*1.0)/(rho*this_cnt)

    
        print '{},{},{}'.format(rho, this_cnt, avg_rate)



scrape_directory(sys.argv[1])
print_final_stats()

