from math import exp

'''
	Yt_1 持仓量
	delta_t delta的和
	lower_gamma 风险偏好度(1~500)
	e 交易成本率,默认0.01
	upper_gamma 总的gamma
	St
	r = 0.02
	T,t

'''
def hedge_determine(Yt_1, delta_t, lower_gamma, upper_gamma, St,  T, t,r=0.02,e=0.01):
	'''
	return how much to buy/sell or to do nothing. 
	Which is worthy of noticing is that the upper_gamma is a
	quantity-weighted gamma of a portfolio
	'''
	#checked
	Bt = ((3 * e * St * exp(-r*(T-t)) * upper_gamma**2) \
		 / (2*lower_gamma))**(1/3)
	lower = delta_t - Bt
	upper = delta_t + Bt
	if  lower <= Yt_1 <= upper: return 0
	elif Yt_1 > upper: return round(upper - Yt_1)
	else: return round(lower - Yt_1)