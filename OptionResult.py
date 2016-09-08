class OptionResult(object):

    @staticmethod
    def getResult(option):
        result = {}
        result["price"] = option.get_price()
        result["delta"] = option.get_delta()
        result["gamma"] = option.get_gamma()
        return result