import sys
import os
import numpy as np

def scrape_first_pass(directory, filename, sums_by_rho_dict):

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
                [start_cnt_str, start_list]      = toks[3].split('-')
                [end_cnt_str, end_list]          = toks[4].split('-')

                x_coord = np.longdouble(location[:-1])

                start_acks = int(start_cnt_str)
                end_acks = int(end_cnt_str)

                start_rho = int(start_density_str) + 1
                end_rho =   int(start_density_str) + 1

                start_time = np.longdouble(start_time_str)
                end_time   = np.longdouble(end_time_str)
                this_pir   = end_time - start_time

                #assert (x_coord < 950), "Drop this packet..."
                assert ((start_rho >= 0) and (end_rho >= 0)),\
                "start_rho={}, end_rho={}".format(start_rho, end_rho)+'\n'+line
                assert ((0 <= start_acks) and (start_acks <= start_rho)),\
                "start_acks={}, start_rho={}".format(start_acks, start_rho)+'\n'+line
                assert ((0 <= end_acks) and (end_acks <= start_rho)),\
                "end_acks={}, start_rho={}".format(end_ackis, start_rho)+'\n'+line

            except Exception as e:
                print e.message,
                print " fuck1"
                continue

            else:

                if start_rho in sums_by_rho_dict:
                    (rate_sum, pir_sum, cnt_now) = sums_by_rho_dict[start_rho]
                    sums_by_rho_dict[start_rho] =\
                        (rate_sum + np.longdouble(end_acks)/start_rho,\
                         pir_sum + this_pir, cnt_now + 1)

                else:
                    #Record new reception number and pir entries
                    sums_by_rho_dict[start_rho] = (np.longdouble(end_acks)/start_rho, this_pir, 1)

def scrape_second_pass(directory, filename, sums_by_rho_dict, stds_by_rho_dict):

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
                [start_cnt_str, start_list]      = toks[3].split('-')
                [end_cnt_str, end_list]          = toks[4].split('-')

                x_coord = np.longdouble(location[:-1])

                start_acks = int(start_cnt_str)
                end_acks = int(end_cnt_str)

                start_rho = int(start_density_str) + 1
                end_rho =   int(start_density_str) + 1

                start_time = np.longdouble(start_time_str)
                end_time   = np.longdouble(end_time_str)
                this_pir   = end_time - start_time

                #assert (x_coord < 950), "Drop this packet..."
                assert ((start_rho >= 0) and (end_rho >= 0)),\
                "start_rho={}, end_rho={}".format(start_rho, end_rho)+'\n'+line
                assert ((0 <= start_acks) and (start_acks <= start_rho)),\
                "start_acks={}, start_rho={}".format(start_acks, start_rho)+'\n'+line
                assert ((0 <= end_acks) and (end_acks <= start_rho)),\
                "end_acks={}, start_rho={}".format(end_acks, start_rho)+'\n'+line

                assert (start_rho in sums_by_rho_dict),\
                "Rho:{} not yet seen?".format(start_rho)

            except Exception as e:
                #print e.message,
                #print " fuck2"
                continue

            else:


                if start_rho in stds_by_rho_dict:
                    (rate_sum, pir_sum, sums_cnt) = sums_by_rho_dict[start_rho]
                    (rate_std, pir_std, stds_cnt) = stds_by_rho_dict[start_rho]

                    this_rate_std = ((np.longdouble(end_acks) / start_rho) - (np.longdouble(rate_sum) / sums_cnt))**2
                    this_pir_std  = (this_pir - (np.longdouble(pir_sum) / sums_cnt))**2

                    stds_by_rho_dict[start_rho] = (rate_std + this_rate_std, pir_std + this_pir_std, stds_cnt + 1)

                else:
                    (rate_sum, pir_sum, sums_cnt) = sums_by_rho_dict[start_rho]

                    this_rate_std = ((np.longdouble(end_acks) / start_rho) - (np.longdouble(rate_sum) / sums_cnt))**2
                    this_pir_std  = (this_pir - (np.longdouble(pir_sum) / sums_cnt))**2

                    stds_by_rho_dict[start_rho] = (this_rate_std, this_pir_std, 1)

def print_final_stats(intro, sums_dict, stds_dict):
    print intro
    print '{},{},{},{},{},{}'.format('rho', 'sz', 'rate', 'rate SD','pir', 'pir SD')
    for rho in sums_dict:

        try:
            assert rho in stds_dict

            (rate_sum, pir_sum, sums_cnt) = sums_dict[rho]
            (rate_std, pir_std, stds_cnt) = stds_dict[rho]

            assert (sums_cnt == stds_cnt), "oops, print_stats: sum={}, std={}".format(sums_cnt, stds_cnt)

        except Exception as e:
            print e.message
            continue
        else:
            if ((rho <= 0) or (sums_cnt <= 1) or (stds_cnt <= 1)):
                print "WHOOPS: rho={}, sums_cnt={}, stds_cnt={}".format(rho, sums_cnt, stds_cnt)
                continue

            avg_rate = rate_sum * 1.0 / sums_cnt
            rate_sd = (rate_std / stds_cnt)**0.5

            avg_pir = pir_sum * 1.0 / sums_cnt
            pir_sd = (pir_std / stds_cnt)**0.5

            print '{:d},{:d},{:0.8f},{:0.8f},{:0.8f},{:0.8f}'.format(rho, sums_cnt, avg_rate, rate_sd, avg_pir, pir_sd)

def scrape_sim_directory(ref_dir, sim_dir):

    sums_by_rho_dict = {}
    stds_by_rho_dict = {}
    toks = sim_dir[:-1].split('_')

    try:
        max_cw   = toks[-1][:-1] #s
        rho      = toks[-2][:-3] #vpm
        avg_vel  = toks[-3][:-3] #mps
        tx_range = toks[-4][:-1] #m

    except Exception as e:
        print e.message,
        print "fuck3"
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


