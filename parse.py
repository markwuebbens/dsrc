import sys
import os

Road_Limit = 500 #m
TX_Range = None

def scrape_first_pass(directory, filename, sums_by_rho_dict):

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
                [start_time_str, end_time_str]       = toks[1].split(' ')
                [start_density_str, end_density_str] = toks[2].split(' ')
                [start_cnt, start_list]      = toks[3].split('-')
                [end_cnt, end_list]          = toks[4].split('-')

                x_coord = float(location[:-1])

                start_nodes = start_list[:-1].split(' ')
                start_rho   = len(start_nodes)
                end_nodes   = end_list[:-1].split(' ')
                acks_rcvd   = len(end_nodes)

                start_time = float(start_time_str)
                end_time   = float(end_time_str)
                this_pir   = end_time - start_time

            except Exception as e:
                print e.message
                print e.args
                sys.exit

            else:

                #Filter messages near the beginning and end of the road
                assert not ((x_coord > (Road_Limit - TX_Range)) or\
                   (x_coord < TX_Range))

                if start_rho < 0:
                    #FIXME
                    print "Weirdness with node {}: {}".format(node_num, line)
                    sys.exit


                if start_rho in sums_by_rho_dict:
                    (rate_sum, pir_sum, cnt_now) = sums_by_rho_dict[start_rho]
                    sums_by_rho_dict[start_rho] = (sum_now + acks_rcvd, pir_sum + this_pir, cnt_now + 1)

                else:
                    #Record new reception number and pir entries
                    sums_by_rho_dict[start_rho] = (acks_rcvd, this_pir, 1)

def scrape_second_pass(directory, filename, sums_by_rho_dict, stds_by_rho_dict):

    global Road_Limit
    global TX_Range

    node_num = filename.split('_')[0]

    with open(directory + filename, 'r') as file:
        for line in file:
            toks = line[:-1].split("|")
            if len(toks) < 5:
                continue
            try:
                [packet_id, location]        = toks[0].split('@')
                [start_time_str, end_time_str]       = toks[1].split(' ')
                [start_density_str, end_density_str] = toks[2].split(' ')
                [start_cnt, start_list]      = toks[3].split('-')
                [end_cnt, end_list]          = toks[4].split('-')

                x_coord = float(location[:-1])

                start_nodes = start_list[:-1].split(' ')
                start_rho   = len(start_nodes)
                end_nodes   = end_list[:-1].split(' ')
                acks_rcvd   = len(end_nodes)

                start_time = float(start_time_str)
                end_time   = float(end_time_str)
                this_pir   = end_time - start_time
            except Exception as e:
                print e.message
                print e.args
                sys.exit
            else:

                assert (start_rho in sums_by_rho_dict)

                if start_rho in stds_by_rho_dict:
                    (rate_sum, pir_sum, sums_cnt) = sums_by_rho_dict[start_rho]
                    (rate_std, pir_std, stds_cnt) = stds_by_rho_dict[start_rho]

                    this_rate_std = (acks_rcvd - (rate_sum * 1.0 / sums_cnt))**2
                    this_pir_std  = (this_pir - (pir_sum * 1.0 / sums_cnt))**2

                    stds_by_rho_dict[start_rho] = (rate_std + this_rate_std, pir_std + this_pir_std, stds_cnt + 1)

                else:
                    (rate_sum, pir_sum, sums_cnt) = sums_by_rho_dict[start_rho]
                    (rate_std, pir_std, stds_cnt) = stds_by_rho_dict[start_rho]

                    this_rate_std = (acks_rcvd - (rate_sum * 1.0 / sums_cnt))**2
                    this_pir_std  = (this_pir - (pir_sum * 1.0 / sums_cnt))**2

                    stds_by_rho_dict[start_rho] = (this_rate_std, this_pir_std, 1)

def print_final_stats(intro, sums_dict, std_dict):
    print intro
    print '{},{},{}'.format('rho', 'sz', 'rate', 'rate SD','pir', 'pir SD')
    for rho in sums_dict:

        assert rho in stds_dict

        (rate_sum, pir_sum, sums_cnt) = sums_dict[rho]
        (rate_std, pir_std, stds_cnt) = stds_dict[rho]

        assert (sums_cnt == stds_cnt), "oops, print_stats: sum={}, std={}".format(sums_cnt, stds_cnt)

        if ((rho <= 0) or (sums_cnt <= 1)):
            print "FIXME!: rho={}, samples={}".format(rho, this_cnt)
            continue

        avg_rate = rate_sum * 1.0 / sums_cnt
        rate_sd = (rate_std / stds_cnt)**0.5

        avg_pir = pir_sum * 1.0 / sums_cnt
        pir_sd = (pir_std / stds_cnt)**0.5

        print '{},{},{},{},{},{}'.format(rho, this_cnt, avg_rate, rate_sd, avg_pir, pir_sd)

def scrape_sim_directory(ref_dir, sim_dir):

    global TX_Range


    sums_by_rho_dict = {}
    stds_by_rho_dict = {}
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
                scrape_first_pass(ref_dir + sim_dir, filename, sums_by_rho_dict)

        for filename in os.listdir(ref_dir + sim_dir):
            if filename.endswith('.log'):
                scrape_second_pass(ref_dir + sim_dir, filename, sums_by_rho_dict, stds_by_rho_dict)

        print_final_stats("\n{}s,{}mps,{}m,{}vpm".format(max_cw, avg_vel, tx_range, rho), sums_by_rho_dict, stds_by_rho_dict)

def scrape_batch(batch_dir):
    for filename in os.listdir(batch_dir):
        if (len(filename.split('_')) == 5):
            scrape_sim_directory(batch_dir, filename + '/')

scrape_batch(sys.argv[1])


