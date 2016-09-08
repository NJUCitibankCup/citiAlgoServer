# -*-coding = utf-8 -*-

from math import exp, log, sqrt, pi
from scipy.stats import norm
import numpy as np
import datetime

class Option(object):
    """arguments:
     type_of_option,    没啥用
     St,
     K,                 行权价格
     T,                 期权售出当日与期货到期日之间的间隔
     t,                 出售之后经过的日期
     r,                 0.02
     q,                 0.02
     sigmma             价格波动率
     """


    def __init__(self, type_of_option, St, K, T, t, sigmma,r=0.02, q=0.02):
        self.type_of_option = type_of_option
        self.St = St
        self.K = K
        self.T = T
        self.t = t
        self.r = r
        self.q = q
        self.sigmma = sigmma

        self.price = 0
        self.delta = 0
        self.gamma = 0

    def _tt(self):
        self.tt = self.T - self.t

    def _sqrttt(self):
        print(self.tt)
        self.sqrttt = sqrt(self.tt)

    def _R(self):
        self.R = exp(-self.r*self.tt)

    def _Q(self):
        self.Q = exp(-self.q*self.tt)

    def norm_pdf_1(self, x):
        return -x/sqrt(2*pi) * exp(-x**2/2)

    def get_price(self):
        return self.price

    def get_delta(self):
        return self.delta

    def get_gamma(self):
        return self.gamma


class EuropeanOption(Option):

    def __init__(self, St, K, T, t, sigmma):
        Option.__init__(self, "Eu", St, K, T, t,sigmma)
        self.__cal()

    def __d1(self):
        self.d1 = 1 / (self.sigmma*self.sqrttt) * (log(self.St / \
        self.K) + (self.r - self.q + self.sigmma**2 / 2)* (self.tt))
        
    def __d2(self):
        self.d2 = self.d1 - self.sigmma * self.sqrttt

    def __d1_1(self):
        self.d1_1 = 1 / (self.St*self.sigmma*self.sqrttt)

    def __d1_2(self):
        self.d1_2 = -1 /(self.St**2 * self.sigmma * self.sqrttt)    

    def __cal_price(self):
        self.price = self.K * self.R * norm.cdf(-self.d2)\
         - self.St * self.Q * norm.cdf(-self.d1)

    def __cal_delta(self):
        self.delta = self.K * self.R * norm.pdf(-self.d2) * (-self.d1_1)\
        -self.Q * norm.cdf(-self.d1) - self.St * self.Q * norm.pdf(-self.d1) * (-self.d1_1)

    def __cal_gamma(self):
        self.gamma = self.K * self.R * (self.norm_pdf_1(-self.d2)*self.d1_1**2 +\
        norm.pdf(-self.d2)*(-self.d1_2)) - self.R * (2*norm.pdf(-self.d1)*(-self.d1_1) +\
        self.St*self.norm_pdf_1(-self.d1)*self.d1_1**2 + self.St*norm.pdf(-self.d1)*(-self.d1_2)) 

    def __cal(self):
        self._tt()
        self._sqrttt()
        self._R()
        self._Q()
        self.__d1()
        self.__d2()
        self.__d1_1()
        self.__d1_2()
        self.__cal_price()
        self.__cal_delta()
        self.__cal_gamma()

    def update_info(self, t, St):
        self.St = St
        self.t = t
        self.__cal()

    def get_d2(self):
        return self.d2


class BarrierOption(Option):

    def __init__(self, St, K, T, t, sigmma, H):  # H is the barrier
        Option.__init__(self, "Ba", St, K, T, t, sigmma)

        self.H = H

        self.equivalent = EuropeanOption(St, K, T, t, sigmma)

        self.__cal()

    def __lamda(self):
        self.lamda = (self.r - self.q + self.sigmma**2 / 2) / self.sigmma**2

    def __x1(self):
        self.x1 = log(self.St / self.H) / (self.sigmma * self.sqrttt) + self.lamda * self.sigmma * self.sqrttt

    def __y(self):
        self.y = log(self.H**2 / (self.St * self.K)) / (self.sigmma * self.sqrttt) + self.lamda * \
        self.sigmma * self.sqrttt

    def __y1(self):
        self.y1 = log(self.H / self.St) / (self.sigmma * self.sqrttt) + self.lamda * self.sigmma * self.sqrttt

    def __x1_1_y_1_y1_1(self):
        self.y1_1 = -1 / self.St / self.sigmma / self.sqrttt
        self.x1_1 = -self.y1_1
        self.y_1 = self.y1_1

    def __x1_2_y_2_y1_2(self):
        self.x1_2 = -1 / (self.St**2 * self.sigmma * self.sqrttt)
        self.y_2 = -self.x1_2
        self.y1_2 = self.y_2

    def __cal_price(self):
        if self.H > self.K:
            self.price = 0
        elif self.H == self.K:
            self.price = self.equivalent.get_price()
        else:               
            self.price = -self.St * norm.cdf(-self.x1) * self.Q + self.K * self.R * norm.cdf(-self.x1 + self.sigmma*self.sqrttt)\
            + self.St * self.Q * (self.H/self.St)**(2*self.lamda) * (norm.cdf(self.y)-norm.cdf(self.y1)) - self.K * self.R * \
            (self.H/self.St)**(2*self.lamda-2) * (norm.cdf(self.y-self.sigmma*self.sqrttt) - norm.cdf(self.y1-self.sigmma*self.sqrttt))
            
    def __cal_delta(self):
        if self.H > self.K:
            self.delta = 0
        elif self.H == self.K:
            self.delta = self.equivalent.get_delta()
        else:
            self.delta = -self.Q * (norm.cdf(-self.x1) - self.St*norm.pdf(-self.x1)*self.x1_1)\
            - self.K * self.R * norm.pdf(-self.x1 + self.gamma*self.sqrttt) * self.x1_1\
            + self.Q * (self.H/self.St)**(2*self.lamda) * ((1-2*self.lamda)*(norm.cdf(self.y)-norm.cdf(self.y1))\
            + self.St*(norm.pdf(self.y_1)*self.y_1 - norm.pdf(self.y1)*self.y1_1))\
            - self.K * self.R * (self.H/self.St)**(2*self.lamda-2)*((2-2*self.lamda)/self.St*(norm.cdf(self.y-self.sigmma*self.sqrttt)\
            - norm.cdf(self.y1-self.sigmma*self.sqrttt)) + norm.pdf(self.y-self.sigmma*self.sqrttt)*self.y_1 - norm.pdf(self.y1-self.sigmma*self.sqrttt)*self.y1_1)

    def __cal_gamma(self):
        if self.H > self.K:
            self.gamma = 0
        elif self.H == self.K:
            self.gamma = self.equivalent.get_gamma()
        else:
            self.gamma = -self.Q * (2*norm.pdf(-self.x1)*(-self.x1_1) + self.St*self.norm_pdf_1(-self.x1)*self.x1_1**2\
            + self.St*norm.pdf(-self.x1)*(-self.x1_2)) + self.K * self.R * (self.norm_pdf_1(-self.x1+self.sigmma*self.sqrttt)*self.x1_1**2
            - norm.pdf(-self.x1+self.sigmma*self.sqrttt)*self.x1_2) + self.Q * (self.H/self.St) ** (2*self.lamda) * ((1-2*self.lamda)*(-2*self.lamda)/self.St\
            * (norm.cdf(self.y)-norm.cdf(self.y1)) - 2*self.lamda*(norm.pdf(self.y)*self.y_1 - norm.pdf(self.y1)*self.y1) + (2-2*self.lamda)*(norm.pdf(self.y)*self.y_1\
            - norm.pdf(self.y1)*self.y1_1) + self.St*(self.norm_pdf_1(self.y)*self.y_1**2+norm.pdf(self.y)*self.y_2-self.norm_pdf_1(self.y1)*self.y1_1**2\
            - norm.pdf(self.y1)*self.y1_2)) - self.K * self.R * (self.H/self.St)**(2*self.lamda-2) * ((((2-2*self.lamda)/self.St)**2 + (2*self.lamda-2)/self.St**2)\
            * (norm.cdf(self.y-self.sigmma*self.sqrttt)-norm.cdf(self.y1-self.sigmma*self.sqrttt)) + (4-4*self.lamda)/self.St * (norm.pdf(self.y-self.sigmma*self.sqrttt)\
            * self.y_1 - norm.pdf(self.y1-self.sigmma*self.sqrttt)*self.y1_1) + self.norm_pdf_1(self.y-self.sigmma*self.sqrttt)*self.y_1**2 + norm.pdf(self.y\
            - self.sigmma*self.sqrttt)*self.y_2 - self.norm_pdf_1(self.y1-self.sigmma*self.sqrttt)*self.y1_1**2 - norm.pdf(self.y1-self.sigmma*self.sqrttt)*self.y1_2)

    def __cal(self):
        self._tt()
        self._sqrttt()
        self._R()
        self._Q()
        self.__lamda()
        self.__x1()
        self.__y()
        self.__y1()  # potential problems of function position!
        self.__x1_1_y_1_y1_1()
        self.__x1_2_y_2_y1_2()
        self.equivalent.update_info(t=self.t, St=self.St)
        self.__cal_price()
        self.__cal_delta()
        self.__cal_gamma()

    def update_info(self, t, St):
        self.St = St
        self.t = t
        self.__cal()
    
'''class AsainOption(Option):

    def __init__(self, type_of_option, St, K, T, t, r, q, sigmma, Fi_series, sigmma_series, time_series):
        Option.__init__(self, type_of_option, St, K, T, t, r, q, sigmma)

        self.Fi_list = Fi_series
        self.sigmma_list = sigmma_series
        self.time_list = time_series

        self.__d1()
        self.__d2()
        self.__M1()
        self.__M2()
        self.sigmma = sqrt(1 / self.T * log(self.M2/self.M1**2))

    def __d1(self):
         self.d1 = 1 / self.sigmma / sqrt(self.T) * (log(self.M1/self.K) + self.sigmma**2 * \
         self.T / 2)

    def __d2(self):
        self.d2 = self.d1 - self.sigmma * sqrt(self.T)

    def __M1(self):
        self.M1 = sum(self.Fi_series)/len(self.Fi_series)

    def __M2(self):
        Fi_array = np.array(self.Fi_list)
        sigmma_array = np.array(self.sigmma_list)
        time_array = np.array(self.time_list)

        term_1 = Fi_array**2 * exp(sigmma_array**2*time_array)
        term_2 = 0
        for j in range(len(self.time_list)):
            for i in range(j):
                term_2 += self.Fi_list[i] * self.Fi_list[j] * \
    			exp(self.sigmma_list[i]**2*self.time_list[i])

    # still do not know the how to get the series!

    	
    def cal_price(self):
        self.price = exp(-self.r * self.T) * (self.K * norm.cdf(-self.d2) - \
        self.M1 * norm.cdf(-self.d1))

    def cal_delta(self):
        pass
'''
'''class BiOption(Option):

    def __init__(self, type_of_option, St, K, T, t, r, q, sigmma, Q):
        Option.__init__(self,type_of_option, St, K, T, t, r, q, sigmma)
        
        self.Q = Q

        self.equivalent = EuropeanOption(type_of_option, St, K, T, t, r, q, sigmma)

        self.d2 = self.equivalent.get_d2()

    def cal_price(self):
        self.price = self.Q * exp(-self.r*(self.T-self.t)) * norm.cdf(-self.d2)
    
    def cal_delta(self):
        self.delta = 0
'''        
def match_option(name_of_type, St, K, T, t, r, q, sigmma, Q, H):    
    #if name_of_type == 'Bi': return BiOption(name_of_type, St, K, T, t, r, q, sigmma, Q)
    if name_of_type == 'Ba': return BarrierOption(name_of_type, St, K, T, t, r, q, sigmma, H)
    elif name_of_type == 'Eu': return EuropeanOption(name_of_type, St, K, T, t, r, q, sigmma)

if __name__ == "__main__":

    before = datetime.datetime.now()
    option_1 = BarrierOption('Ba', 20, 5, 2, 0.8, 0.1, 0.2, 2, 15)
    after = datetime.datetime.now()
    print((after-before).microseconds)
    print("anaconda is installed")