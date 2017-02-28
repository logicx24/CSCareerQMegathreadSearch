from flask import Flask, request, jsonify, render_template
#import logging 

import periodicUpdate
import searchingInfra

app = Flask(__name__)
ix = searchingInfra.genIndex()

#logging.basicConfig(filename='app.log',level=logging.DEBUG)

@app.route("/")
def test():
	return render_template("index.html")

@app.route("/search", methods=["POST"])
def searchRoute():
	search_results = searchingInfra.search(ix, request.form['query'])
	return jsonify(search_results)

if __name__ == "__main__":
	periodicUpdate.backgroundThread()
	app.run()
	
