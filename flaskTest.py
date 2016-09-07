from flask import Flask,jsonify
from bl.Option import *
import OptionResult

app = Flask(__name__)


@app.route('/')
def hello_world():
    return 'Hello World!'

@app.route("/test")
def testDelta():
    option_1 = EuropeanOption(St=4009, K=8000, T=100, t=20, sigmma=7)
    result = {}
    result["price"] = option_1.get_price()
    result["delta"] = option_1.get_delta()
    return jsonify(result)

@app.route("/option/Eu")
def computeEu():


if __name__ == '__main__':
    app.run()
