import multiprocessing as mp
from math import log
from math import floor
from math import exp
import pandas as pd


queue_toconsume = mp.Queue(1000000)  # (i, j, k)
queue_toproduce = mp.Queue()  # ((i, j, k), s)
queue_inter = mp.Queue()  # ((i, j, k), s)

total_length_of_queue_toconsume = mp.Value('i', 0)

event_start_produce = mp.Event()
event_start_consume2 = mp.Event()

#These consts describe where the .csv files located
#------------------------------------------------------
PATH = "a_2010.csv"
PRICE_DATA_RANGE = (652, 892)
# PRICE_DATA_RANGE = (652, 653)
PRICE_DATA_COLUMN = 8
#------------------------------------------------------


#How the intervals and gaps are decreasing
#------------------------------------------------------
INTERVAL_DIVIDER = 4
GAP_DIVIDER = 2
#------------------------------------------------------


#Initial settings about omega, alpha, beta ranges
#--------------------------------------------------------------
ORIG_OMEGA_RANGE = (1, 100000000)  # denominated 10e-9
ORIG_ALPHA_RANGE = (-100000, 100000)  # demonicated 10e-6
ORIG_BETA_RANGE = (-100000, 100000)  # denominated 10e-6
RATE_GAP_TO_INTERVAL_O = 100
RATE_GAP_TO_INTERVAL_AB = 50
SEED = (((ORIG_OMEGA_RANGE[1] - ORIG_OMEGA_RANGE[0]) // 2,
         (ORIG_ALPHA_RANGE[1] - ORIG_ALPHA_RANGE[0]) // 2,
         (ORIG_BETA_RANGE[1] - ORIG_BETA_RANGE[0]) // 2), 0.0)
#--------------------------------------------------------------


# initialize intervals for o, a, b
#---------------------------------------------------------
interval_o = mp.Value('i', (ORIG_OMEGA_RANGE[1] - ORIG_OMEGA_RANGE[0]) // 2)
interval_ab = mp.Value('i', (ORIG_ALPHA_RANGE[1] - ORIG_ALPHA_RANGE[0]) // 2)

gap_o = mp.Value('i', interval_o.value // RATE_GAP_TO_INTERVAL_O)
gap_ab = mp.Value('i', interval_ab.value // RATE_GAP_TO_INTERVAL_AB)

result_o = mp.Value('i', 0)
result_a = mp.Value('i', 0)
result_b = mp.Value('i', 0)
result_s = mp.Value('d', 0.0)
#---------------------------------------------------------


# This segment intends to generate price_list and u_list
#---------------------------------------------------------
'''to get a list of price'''
df_tmp = pd.read_csv(PATH, encoding='EUC-CN', index_col=0)
price_list = df_tmp.iloc[PRICE_DATA_RANGE[0]:PRICE_DATA_RANGE[1], PRICE_DATA_COLUMN].values.tolist()
del df_tmp

'''to generate u_list'''
u_list = []
for i in range(len(price_list)):
    if i == 0:
        u_list.append('na')
    else:
        u_list.append(log(price_list[i] / price_list[i - 1]))
#---------------------------------------------------------


def dots_generator(interval, gap):
    return [i for i in range(interval[0], interval[1] + 1, gap)]


def boarder_decider(initial_set, new_set):
    return (max(initial_set[0], new_set[0]), min(initial_set[1], new_set[1]))


def producer():
    '''to give a point and then generates several dots, 
    quit when interval = 1'''
    while 1:
        event_start_produce.wait()

        if interval_o.value == 0 and interval_ab.value == 0:
            if queue_toproduce.qsize() == 1:
                print("finish")
                to_return = queue_toproduce.get()
                result_o.value, result_a.value, result_b.value = to_return[0]
                result_s.value = to_return[1]
                return to_return
            else: 
                for i in range(queue_toproduce.qsize()):
                    queue_toconsume.put(queue_toproduce.get())
                    event_start_produce.clear()
                    continue

        interval_t_o = interval_o.value
        interval_t_ab = interval_ab.value

        total_length_of_queue_toconsume.value = 0

        omega, alpha, beta = queue_toproduce.get()[0]
        
        omega_interval = boarder_decider(ORIG_OMEGA_RANGE, (omega - interval_t_o, omega + interval_t_o))
        alpha_interval = boarder_decider(ORIG_ALPHA_RANGE, (alpha - interval_t_ab, alpha + interval_t_ab))
        beta_interval = boarder_decider(ORIG_BETA_RANGE, (beta - interval_t_ab, beta + interval_t_ab))

        omega_dots_list = []
        if gap_o.value == 0:
            omega_dots_list.append(omega)
        else:
            omega_dots_list = dots_generator(omega_interval, gap_o.value)

        alpha_dots_list = []
        beta_dots_list = []
        if gap_ab.value == 0:
            alpha_dots_list.append(alpha)
            beta_dots_list.append(beta)
        else:
            alpha_dots_list = dots_generator(alpha_interval, gap_ab.value)
            beta_dots_list = dots_generator(beta_interval, gap_ab.value)

        # to put (omega, alpha, beta) into queue
        #-----------------------------------------------------------------
        total_length_of_queue_toconsume.value = len(omega_dots_list) * len(alpha_dots_list) * len(beta_dots_list)
        print("total length:" + str(total_length_of_queue_toconsume.value))

        event_start_consume2.set()
        for i in omega_dots_list:
            for j in alpha_dots_list:
                for k in beta_dots_list:
                    queue_toconsume.put((i, j, k))
                    
        # to reduce the interval and gap
        #----------------------------------------------------------------
        interval_o.value //= INTERVAL_DIVIDER
        interval_ab.value //= INTERVAL_DIVIDER

        gap_o.value = max(gap_o.value // GAP_DIVIDER, 1)
        gap_ab.value = max(gap_ab.value // GAP_DIVIDER, 1)

        event_start_produce.clear()


def calculator_consumer():
    '''receive a set of: (omega, alpha, beta), return its s_value in
    a queue ((omega, alpha, beta), s_value)'''
    while 1:
        omega, alpha, beta = queue_toconsume.get()
        #if alpha + beta >= 1000:
        #    queue_inter.put(((omega, alpha, beta), 0.0))
        #    continue
       
        omega_real = omega / 100000000
        alpha_real = alpha / 100000
        beta_real = beta / 100000

        sigmmasqr_list = []
        s_value = 0
        sumi = 0


        for i in range(len(price_list)):
            if i == 0:
                sigmmasqr_list.append('na')
            elif i == 1:
                sigmmasqr_list.append('na')
            elif i == 2:
                sigmmasqr_list.append(u_list[i - 1]**2)
                s_value = -log(sigmmasqr_list[i]) - \
                    u_list[i - 1]**2 / sigmmasqr_list[i]
                sumi = sumi + s_value
            else:
                this_sigmmasqr = omega_real + alpha_real * \
                    u_list[i - 1]**2 + beta_real * sigmmasqr_list[i - 1]
                if this_sigmmasqr <= 0:                                  
                    queue_inter.put(((omega, alpha, beta), 0.0))
                    break 
                sigmmasqr_list.append(this_sigmmasqr)
                s_value = -log(sigmmasqr_list[i]) - u_list[i - 1]**2 / sigmmasqr_list[i]
                sumi = sumi + s_value

        queue_inter.put(((omega, alpha, beta), sumi))


def subscriber_consumer2():
    while 1:
        event_start_consume2.wait()
        target_set = SEED
        count = 1
        total = total_length_of_queue_toconsume.value
        while count <= total:
            this_set = queue_inter.get()
            count += 1
            if this_set[1] > target_set[1]:
                target_set = this_set
            
        queue_toproduce.put(target_set)
        event_start_consume2.clear()
        event_start_produce.set()

def expect_sigmma_t(omega, alpha, beta, sigmma_n, t_in_year):
	return omega + (alpha + beta)**t_in_year * (sigmma_n**2 - omega)

def average_sigmma_till_t(omega, alpha, beta, sigmma_n, t):
	return omega + (1 - exp(-alpha*t)/(alpha*t)) * (sigmma_n - omega)


def estimate_args():
    producer_1 = mp.Process(target=producer)
    consumer_1 = [mp.Process(target=calculator_consumer) for i in range(2)]
    consumer_2 = mp.Process(target=subscriber_consumer2)

    event_start_produce.set()
    queue_toproduce.put(SEED)

    consumer_2.start()
    producer_1.start()
    for i in consumer_1:
        i.start()

    producer_1.join()

    print(result_o.value, result_a.value, result_b.value, result_s.value)
    print(expect_sigmma_t(result_o.value/1e9, result_a.value/1e6, result_b.value/1e6, sigmma_n=3, t_in_year=120/252))

    for i in consumer_1:
        i.terminate()
    consumer_2.terminate()


if __name__ == "__main__":
    estimate_args()

