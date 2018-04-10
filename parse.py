import sys
import os

def scrape_sim_directory(ref_dir, sim_dir):

    Road_Limit = 500 #m
    TX_Range = None

    def scrape_node(directory, filename, rho_dict):

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
                    if (x_coord > (Road_Limit - 2*TX_Range)) or\
                       (x_coord < TX_Range):
                        #Filter messages near the end of the road
                        continue
                    if this_density <= 0:
                        #FIXME
                        print "Weirdness: {}".format(line)
                        continue
                    elif this_density in rho_dict:
                        (sum_now, cnt_now) = rho_dict[this_density]
                        rho_dict[this_density] = (sum_now + len(end_nodes), cnt_now + 1)

                    else:
                        rho_dict[this_density] = (len(end_nodes), 1)

    def print_final_stats(intro, rho_dict):
        print intro
        print '{},{},{}'.format('rho', 'sz', 'rate')
        for rho in rho_dict:

            (this_sum, this_cnt) = rho_dict[rho]

            if (rho*this_cnt <= 0):
                print "FIXME!: rho={}, samples={}".format(rho, this_cnt)
                continue

            avg_rate = (this_sum*1.0)/(rho*this_cnt)


            print '{},{},{}'.format(rho, this_cnt, avg_rate)

    Sum_Cnt_By_Rho_dict = {}
    toks = sim_dir[:-1].split('_')

    try:
        max_cw   = toks[-1][:-1] #s
        rho      = toks[-2][:-3] #vpm
        avg_vel  = toks[-3][:-3] #mps
        tx_range = toks[-4][:-1] #m

        TX_Range = float(tx_range)

    except Exception as e:
        print e.message
        print e.args
        sys.exit

    else:
        for filename in os.listdir(ref_dir + sim_dir):
            if filename.endswith('.log'):
                scrape_node(ref_dir + sim_dir, filename, Sum_Cnt_By_Rho_dict)

        print_final_stats("\n{}s,{}mps,{}m,{}vpm".format(max_cw, avg_vel, tx_range, rho), Sum_Cnt_By_Rho_dict)

def scrape_batch(batch_dir):
    for filename in os.listdir(batch_dir):
        scrape_sim_directory(batch_dir, filename + '/')

scrape_batch(sys.argv[1])


