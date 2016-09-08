from flask import Flask,jsonify,request,json
from bl.Option import *
from OptionResult import OptionResult
from bl.DeltaDateComputer import DeltaDateComputer
from bl.SigmmaEstimater import SigmmaEstimater

app = Flask(__name__)


@app.route('/')
def hello_world():
    return 'Hello World!'


@app.route("/test")
def testDelta():
    option_1 = EuropeanOption(St=4009, K=8000, T=100/252, t=20/252, sigmma=7)
    result = {}
    result["price"] = option_1.get_price()
    result["delta"] = option_1.get_delta()
    return jsonify(result)

@app.route("/option/sigmma",methods=["POST"])
def computeSigmma():
    priceListJson = request.form["priceList"]
    priceList = json.loads(priceListJson)
    return str(SigmmaEstimater(priceList).estimate())
    # return str(3.2)

@app.route("/option/Eu")
def computeEu():
    St, K, T, t, sigmma = __convertOptionArgs()
    option = EuropeanOption(St,K,T,t,sigmma)
    return jsonify(OptionResult.getResult(option))

@app.route("/option/Ba")
def computeBa():
    St, K, T, t, sigmma = __convertOptionArgs()
    H = float(request.args["H"])
    option = BarrierOption(St, K, T, t, sigmma,H)
    return jsonify(OptionResult.getResult(option))

def __convertOptionArgs():
    St = float(request.args["St"])
    K = float(request.args["K"])
    startDateString = request.args["startDate"]
    endDateString = request.args["endDate"]
    sigmma = float(request.args["sigmma"])
    T, t = DeltaDateComputer.compute(startDateString, endDateString)
    return (St,K,T,t,sigmma)

if __name__ == "__main__":
    app.run(debug=True)