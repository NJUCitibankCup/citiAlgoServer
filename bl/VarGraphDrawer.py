from scipy.stats import norm
from bl.Option import *
from math import floor
import multiprocessing as mp
import copy
import matplotlib.pyplot as plt

import datetime

class VarGraphDrawer:

	def __init__(self):
		self.TOTAL_YEAR = 252
		self.R = 0.02


	@staticmethod
	def __hedge_determine(Yt_1, delta_t, lower_gamma, e, upper_gamma, St, r, T, t):
		"""
		return how much to buy/sell or to do nothing.
		Which is worthy of noticing is that the upper_gamma is a
		quantity-weighted gamma of a portfolio
		"""
		#checked
		Bt = ((3 * e * St * exp(-r*(T-t)) * upper_gamma**2) \
			 / (2*lower_gamma))**(1/3)
		lower = delta_t - Bt
		upper = delta_t + Bt
		if  lower <= Yt_1 <= upper: return 0
		elif Yt_1 > upper: return round(upper - Yt_1)
		else: return round(lower - Yt_1)

	def __one_curve(self, count, p_list, option_list, x, days, f_quant, lower_gamma):
		'''
		to calculate the total
		'''

		St_1 = x
		trade_history = []
		St_history = []

		for i in range(days):
			e = norm.rvs(1)
			St = St_1 * exp(((self.R-self.SIGMMA**2/2) * 1/self.TOTAL_YEAR
							 + self.SIGMMA*e*sqrt(1/self.TOTAL_YEAR)))
			St_history.append(St)

			total_delta = 0
			total_gamma = 0
			for option in option_list:
				if option.type_of_option in ("Eu", "Ba"):
					option.update_info(t=option.t+1/252, St=St)
				else:
					if not (i % 20):
						option.update_info(Fi=St, Ti=option.t+1/252, sigmma_i=self.SIGMMA)
				total_delta += option.get_delta()
				total_gamma += option.get_gamma()
				change = self.__hedge_determine(
					Yt_1=f_quant, delta_t=total_delta,
					lower_gamma=lower_gamma, upper_gamma=total_gamma,
					St=St, r=self.R, T=days/self.TOTAL_YEAR, t=(i+1)/self.TOTAL_YEAR, e=0.04
					)
				f_quant += change
				trade_history.append(f_quant)
				St_1 = St

		total_value = St_1 * f_quant
		for option in option_list:
			total_value += option.get_price()
		# print(total_value)
		p_list.append(total_value)


	def start(self, args):
		i, days, option_list, x, f_quant, lower_gamma, percentage, result_list = args
		p_list = []
		self.__one_curve(i, p_list, option_list, x, days, f_quant, lower_gamma)
		p_list.sort()
		print("Finished!")
		result_list.append(p_list[max(floor(len(p_list)*percentage), 0)])

	def compute(self,optionList):
		self.SIGMMA = optionList[0].sigmma
		pool = mp.Pool()
		manager = mp.Manager()
		result_list = manager.list()

		lower_gamma_lst = list(range(1, 1510, 50))
		to_in = ((i, 20, copy.deepcopy(optionList), 3970, 0, i, 0.05, result_list) for i in lower_gamma_lst)
		pool.map(self.start, to_in)

		pool.close()
		pool.join()

		result_list.sort(reverse=True)
		result_list = [i for i in result_list]
		return (lower_gamma_lst,result_list)
		# plt.plot(lower_gamma_lst, result_list, 'b-')
		# print(result_list)
		# plt.show()

if __name__=="__main__":
	sigmma = 7.4
	option1 = [BarrierOption(St=3970, K=3900, T=240/252, t=0, sigmma=sigmma,H=10000) for i in range(5)]
	# option1 = [EuropeanOption(St=4000, K=2000, T=240 / 252, t=0, sigmma=sigmma) for i in range(5)]

	before = datetime.datetime.now()

	lower_gamma_lst,result_list = VarGraphDrawer().compute(option1)

	after = datetime.datetime.now()
	print("delta time : " + str((after - before).seconds))

	plt.plot(lower_gamma_lst, result_list, 'b-')
	# print(result_list)
	plt.show()
