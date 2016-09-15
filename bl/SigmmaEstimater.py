import multiprocessing as mp
from math import log
from math import floor
from math import exp
import pandas as pd
import json
import datetime

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

        self.INTERVAL_DIVIDER_O = 11
        self.INTERVAL_DIVIDER_AB = 6
        self.GAP_DIVIDER_O = 11
        self.GAP_DIVIDER_AB = 6

        self.ORIG_OMEGA_RANGE = (1, 1000000)  # denominated 10e-9
        self.ORIG_ALPHA_RANGE = (-1000, 1000)  # demonicated 10e-6
        self.ORIG_BETA_RANGE = (-1000, 1000)  # denominated 10e-6
        self.NUM_O = 20
        self.NUM_AB = 10
        self.SEED = (((self.ORIG_OMEGA_RANGE[1] - self.ORIG_OMEGA_RANGE[0]) // 2,
                 (self.ORIG_ALPHA_RANGE[1] - self.ORIG_ALPHA_RANGE[0]) // 2,
                 (self.ORIG_BETA_RANGE[1] - self.ORIG_BETA_RANGE[0]) // 2), 0.0)

        self.interval_o = mp.Value('i', (self.ORIG_OMEGA_RANGE[1] - self.ORIG_OMEGA_RANGE[0]) // 2)
        self.interval_ab = mp.Value('i', (self.ORIG_ALPHA_RANGE[1] - self.ORIG_ALPHA_RANGE[0]) // 2)

        self.gap_o = mp.Value('i', self.interval_o.value // self.NUM_O)
        self.gap_ab = mp.Value('i', self.interval_ab.value // self.NUM_AB)

        self.result_o = mp.Value('i', 0)
        self.result_a = mp.Value('i', 0)
        self.result_b = mp.Value('i', 0)
        self.result_s = mp.Value('d', 0.0)

        self.price_list = [i for i in price_list if i > 0];
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
                if self.queue_toproduce.qsize() == 1:
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

            omega_dots_list = [omega]  # !!!!!!
            alpha_dots_list = [alpha]  # !!!!!!
            beta_dots_list = [beta]  # !!!!!!

            omega_dots_list = self.dots_generator(omega_interval, self.gap_o.value)  # !!!!!!
            alpha_dots_list = self.dots_generator(alpha_interval, self.gap_ab.value)  # !!!!!!
            beta_dots_list = self.dots_generator(beta_interval, self.gap_ab.value)  # !!!!!!
            # omega_dots_list = []
            # if self.gap_o.value == 0:
            #     omega_dots_list.append(omega)
            # else:
            #     omega_dots_list = self.dots_generator(omega_interval, self.gap_o.value)
            #
            # alpha_dots_list = []
            # beta_dots_list = []
            # if self.gap_ab.value == 0:
            #     alpha_dots_list.append(alpha)
            #     beta_dots_list.append(beta)
            # else:
            #     alpha_dots_list = self.dots_generator(alpha_interval, self.gap_ab.value)
            #     beta_dots_list = self.dots_generator(beta_interval, self.gap_ab.value)

            # to put (omega, alpha, beta) into queue
            #-----------------------------------------------------------------
            self.total_length_of_queue_toconsume.value = len(omega_dots_list) * len(alpha_dots_list) * len(beta_dots_list)

            self.event_start_consume2.set()
            for i in omega_dots_list:
                for j in alpha_dots_list:
                    for k in beta_dots_list:
                        self.queue_toconsume.put((i, j, k))
                        #print(i, j, k)

            # to reduce the interval and gap
            #----------------------------------------------------------------
            # self.interval_o.value //= self.INTERVAL_DIVIDER_O
            # self.interval_ab.value //= self.INTERVAL_DIVIDER_AB
            #
            # self.gap_o.value = max(self.gap_o.value // self.GAP_DIVIDER_o, 0)
            # self.gap_ab.value = max(self.gap_ab.value // self.GAP_DIVIDER_ab, 0)
            #
            # self.event_start_produce.clear()

            self.interval_o.value //= self.INTERVAL_DIVIDER_O  # !!!!!!
            self.interval_ab.value //= self.INTERVAL_DIVIDER_AB  # !!!!!!

            self.gap_o.value = max(self.gap_o.value // self.GAP_DIVIDER_O, 1)  # !!!!!!
            self.gap_ab.value = max(self.gap_ab.value // self.GAP_DIVIDER_AB, 1)  # !!!!!!


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
        history_large_set = ((0, 0, 0), 0.0)  # !!!!!!
        while 1:
            self.event_start_consume2.wait()
            target_set = self.SEED
            count = 1
            total = self.total_length_of_queue_toconsume.value
            while count <= total:
                this_set = self.queue_inter.get()
                count += 1
                if this_set[1] > target_set[1]:
                    target_set = this_set

            if target_set[1] > history_large_set[1]:  # !!!!!!
                self.queue_toproduce.put(target_set)  # !!!!!!
                history_large_set = target_set  # !!!!!!
            else:  # !!!!!!
                self.queue_toproduce.put(history_large_set)  # !!!!!!

            self.event_start_consume2.clear()
            self.event_start_produce.set()

    @staticmethod
    def __expect_sigmma_t(omega, alpha, beta, sigmma_n, t_in_year):
        return omega + (alpha + beta)**t_in_year * (sigmma_n**2 - omega)

    @staticmethod
    def __average_sigmma_till_t(omega, alpha, beta, sigmma_n, t):
        return omega + (1 - exp(-alpha*t)/(alpha*t)) * (sigmma_n - omega)

    def estimate(self):
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
        print("estimate end")
        return sigmma

if __name__ == "__main__":

    before = datetime.datetime.now()
    # test_list = [4009, 4066, 4014, 3933, 3976, 3934, 3862, 3882, 3870, 3855, 3867, 3829, 3820, 3810, 3839, 3835, 3842, 3796, 3792, 3731, 3697, 3709, 3690, 3715, 3748, 3749, 3714, 3732, 3714, 3733, 3772, 3774, 3774, 3766, 3798, 3803, 3812, 3786, 3760, 3783, 3789, 3792, 3794, 3760, 3756, 3774, 3795, 3788, 3810, 3818, 3837, 3813, 3815, 3799, 3821, 3833, 3837, 3813, 3825, 3831, 3852, 3879, 3880, 3915, 3924, 3948, 3937, 3955, 3928, 3951, 3969, 3985, 3995, 3993, 3969, 3940, 3957, 3965, 3963, 4006, 3995, 3923, 3944, 3936, 3958, 3952, 3933, 3851, 3856, 3842, 3851, 3866, 3879, 3856, 3862, 3868, 3878, 3844, 3821, 3818, 3831, 3844, 3788, 3806, 3784, 3807, 3798, 3829, 3830, 3868, 3867, 3862, 3861, 3845, 3854, 3851, 3821, 3819, 3827, 3825, 3804, 3811, 3848, 3854, 3861, 3844, 3843, 3857, 3882, 3871, 3875, 3883, 3871, 3883, 3894, 3870, 3865, 3883, 3905, 3956, 3950, 3946, 3928, 3919, 3965, 3944, 3938, 3935, 3962, 3989, 3974, 3996, 3957, 3901, 3894, 3885, 3866, 3871, 3887, 3922, 3879, 3870, 3867, 3885, 3928, 3934, 3942, 3903, 3889, 3882, 3884, 3887, 3885, 3886, 3984, 3955, 4034, 3994, 3984, 3975, 3957, 4113, 4080, 4094, 4108, 4106, 4070, 4075, 4059, 4117, 4109, 4156, 4141, 4092, 4074, 4043, 4092, 4093, 4100, 4130, 4221, 4244, 4241, 4296, 4300, 4197, 4164, 4134, 4001, 3999, 4017, 3990, 3997, 4009, 4015, 3980, 3957, 3955, 3964, 3991, 3999, 4013, 3980, 3963, 3968, 3962, 3966, 3980, 3963, 3949, 3951, 3960, 3950, 3944, 3941, 3976, 3990, 3995, 3997, 4003, 4040, 4006]
    # test_list = [4005,4008,4005,4009]*40
    test_list = [4005]*100

    print(SigmmaEstimater(test_list).estimate())
    after = datetime.datetime.now()

    print("delta time : "+str((after-before).seconds))
