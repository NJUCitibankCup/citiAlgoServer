from math import exp

def hedge_determine(Yt_1, delta_t, lower_gamma, e, upper_gamma, St, r, T, t):
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