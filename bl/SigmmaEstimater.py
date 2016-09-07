import multiprocessing as mp
from math import log
from math import floor
from math import exp
import pandas as pd
import json

class SigmmaEstimater(object):

    def __init__(self,price_list):
        self.queue_toconsume = mp.Queue(1000000)  # (i, j, k)
        self.queue_toproduce = mp.Queue()  # ((i, j, k), s)
        self.queue_inter = mp.Queue()  # ((i, j, k), s)

        self.total_length_of_queue_toconsume = mp.Value('i', 0)

        self.event_start_produce = mp.Event()
        self.event_start_consume2 = mp.Event()

        self.PATH = "a_2010.csv"
        self.PRICE_DATA_RANGE = (652, 894)
        self.PRICE_DATA_COLUMN = 8

        self.INTERVAL_DIVIDER = 4
        self.GAP_DIVIDER_o = 3
        self.GAP_DIVIDER_ab = 3

        self.ORIG_OMEGA_RANGE = (1, 1000000)  # denominated 10e-9
        self.ORIG_ALPHA_RANGE = (-1000, 1000)  # demonicated 10e-6
        self.ORIG_BETA_RANGE = (-1000, 1000)  # denominated 10e-6
        self.RATE_GAP_TO_INTERVAL_O = 20
        self.RATE_GAP_TO_INTERVAL_AB = 15
        self.SEED = (((self.ORIG_OMEGA_RANGE[1] - self.ORIG_OMEGA_RANGE[0]) // 2,
                 (self.ORIG_ALPHA_RANGE[1] - self.ORIG_ALPHA_RANGE[0]) // 2,
                 (self.ORIG_BETA_RANGE[1] - self.ORIG_BETA_RANGE[0]) // 2), 0.0)

        self.interval_o = mp.Value('i', (self.ORIG_OMEGA_RANGE[1] - self.ORIG_OMEGA_RANGE[0]) // 2)
        self.interval_ab = mp.Value('i', (self.ORIG_ALPHA_RANGE[1] - self.ORIG_ALPHA_RANGE[0]) // 2)

        self.gap_o = mp.Value('i', self.interval_o.value // self.RATE_GAP_TO_INTERVAL_O)
        self.gap_ab = mp.Value('i', self.interval_ab.value // self.RATE_GAP_TO_INTERVAL_AB)

        self.result_o = mp.Value('i', 0)
        self.result_a = mp.Value('i', 0)
        self.result_b = mp.Value('i', 0)
        self.result_s = mp.Value('d', 0.0)

        self.price_list = price_list
        self.u_list = []
        for i in range(len(self.price_list)):
            if i == 0:
                self.u_list.append('na')
            else:
                self.u_list.append(log(self.price_list[i] / self.price_list[i - 1]))

    @staticmethod
    def dots_generator(interval, gap):
        return [i for i in range(interval[0], interval[1] + 1, gap)]

    @staticmethod
    def boarder_decider(initial_set, new_set):
        return (max(initial_set[0], new_set[0]), min(initial_set[1], new_set[1]))

    def producer(self):
        """"to give a point and then generates several dots,
        quit when interval = 1"""
        while 1:
            self.event_start_produce.wait()

            if self.interval_o.value == 0 and self.interval_ab.value == 0:
                print("ready to end.")
                print(self.queue_toconsume.qsize())
                if self.queue_toproduce.qsize() == 1:
                    print("finish")
                    to_return = self.queue_toproduce.get()
                    self.result_o.value, self.result_a.value, self.result_b.value = to_return[0]
                    self.result_s.value = to_return[1]
                    return to_return
                else:
                    for i in range(self.queue_toproduce.qsize()):
                        self.queue_toconsume.put(self.queue_toproduce.get())
                        self.event_start_produce.clear()
                        continue

            self.interval_t_o = self.interval_o.value
            self.interval_t_ab = self.interval_ab.value

            self.total_length_of_queue_toconsume.value = 0

            omega, alpha, beta = self.queue_toproduce.get()[0]

            omega_interval = self.boarder_decider(self.ORIG_OMEGA_RANGE, (omega - self.interval_t_o, omega + self.interval_t_o))
            alpha_interval = self.boarder_decider(self.ORIG_ALPHA_RANGE, (alpha - self.interval_t_ab, alpha + self.interval_t_ab))
            beta_interval = self.boarder_decider(self.ORIG_BETA_RANGE, (beta - self.interval_t_ab, beta + self.interval_t_ab))

            omega_dots_list = []
            if self.gap_o.value == 0:
                omega_dots_list.append(omega)
            else:
                omega_dots_list = self.dots_generator(omega_interval, self.gap_o.value)

            alpha_dots_list = []
            beta_dots_list = []
            if self.gap_ab.value == 0:
                alpha_dots_list.append(alpha)
                beta_dots_list.append(beta)
            else:
                alpha_dots_list = self.dots_generator(alpha_interval, self.gap_ab.value)
                beta_dots_list = self.dots_generator(beta_interval, self.gap_ab.value)

            # to put (omega, alpha, beta) into queue
            #-----------------------------------------------------------------
            self.total_length_of_queue_toconsume.value = len(omega_dots_list) * len(alpha_dots_list) * len(beta_dots_list)
            print("total length:" + str(self.total_length_of_queue_toconsume.value))
            print("intervals:"+str((self.interval_o.value, self.interval_ab.value)))
            print("gaps:"+str((self.gap_o.value, self.gap_ab.value)))

            self.event_start_consume2.set()
            for i in omega_dots_list:
                for j in alpha_dots_list:
                    for k in beta_dots_list:
                        self.queue_toconsume.put((i, j, k))
                        #print(i, j, k)

            # to reduce the interval and gap
            #----------------------------------------------------------------
            self.interval_o.value //= self.INTERVAL_DIVIDER
            self.interval_ab.value //= self.INTERVAL_DIVIDER

            self.gap_o.value = max(self.gap_o.value // self.GAP_DIVIDER_o, 0)
            self.gap_ab.value = max(self.gap_ab.value // self.GAP_DIVIDER_ab, 0)

            self.event_start_produce.clear()


    def calculator_consumer(self):
        '''receive a set of: (omega, alpha, beta), return its s_value in
        a queue ((omega, alpha, beta), s_value)'''
        while 1:
            omega, alpha, beta = self.queue_toconsume.get()

            omega_real = omega / 1000000
            alpha_real = alpha / 1000
            beta_real = beta / 1000

            sigmmasqr_list = []
            s_value = 0
            sumi = 0

            for i in range(len(self.price_list)):
                if i == 0:
                    sigmmasqr_list.append('na')
                elif i == 1:
                    sigmmasqr_list.append('na')
                elif i == 2:
                    sigmmasqr_list.append(self.u_list[i - 1]**2)
                    s_value = -log(sigmmasqr_list[i]) - \
                        self.u_list[i - 1]**2 / sigmmasqr_list[i]
                    sumi = sumi + s_value
                else:
                    this_sigmmasqr = omega_real + alpha_real * \
                        self.u_list[i - 1]**2 + beta_real * sigmmasqr_list[i - 1]
                    if this_sigmmasqr <= 0:
                        self.queue_inter.put(((omega, alpha, beta), 0.0))
                        break
                    sigmmasqr_list.append(this_sigmmasqr)
                    s_value = -log(sigmmasqr_list[i]) - self.u_list[i - 1]**2 / sigmmasqr_list[i]
                    sumi = sumi + s_value

            self.queue_inter.put(((omega, alpha, beta), sumi))

    def subscriber_consumer2(self):
        while 1:
            self.event_start_consume2.wait()
            target_set = self.SEED
            count = 1
            total = self.total_length_of_queue_toconsume.value
            print("total_length_get:%d" % total)
            while count <= total:
                this_set = self.queue_inter.get()
                count += 1
                if this_set[1] > target_set[1]:
                    target_set = this_set
            self. queue_toproduce.put(target_set)
            self.event_start_consume2.clear()
            self.event_start_produce.set()

    @staticmethod
    def __expect_sigmma_t(omega, alpha, beta, sigmma_n, t_in_year):
        return omega + (alpha + beta)**t_in_year * (sigmma_n**2 - omega)

    @staticmethod
    def __average_sigmma_till_t(omega, alpha, beta, sigmma_n, t):
        return omega + (1 - exp(-alpha*t)/(alpha*t)) * (sigmma_n - omega)

    def estimate_args(self):
        producer_1 = mp.Process(target=self.producer)
        consumer_1 = [mp.Process(target=self.calculator_consumer) for i in range(1)]
        consumer_2 = mp.Process(target=self.subscriber_consumer2)

        self.event_start_produce.set()
        self.queue_toproduce.put(self.SEED)

        consumer_2.start()
        producer_1.start()
        for i in consumer_1:
            i.start()

        producer_1.join()
        # print(self.result_o.value, self.result_a.value, self.result_b.value, self.result_s.value)
        sigmma = self.__expect_sigmma_t(self.result_o.value / 1e7,
             self.result_a.value / 1e4,
             self.result_b.value / 1e4,
             sigmma_n=3, t_in_year=20 / 252)

        for i in consumer_1:
            i.terminate()
        consumer_2.terminate()

        return sigmma

if __name__ == "__main__":

    with open('test_list.json', 'r') as f:
        test_list = json.load(f)

    print(SigmmaEstimater(test_list).estimate_args())

