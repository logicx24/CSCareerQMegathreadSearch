from datetime import datetime
from flask import Flask, request, jsonify, render_template
#import logging 

import periodicUpdate
import searchingInfra
import commentFinder

from config_dict import config


app = Flask(__name__)
ix = searchingInfra.genIndex()

#logging.basicConfig(filename='app.log',level=logging.DEBUG)

def mongoConn():
	return pymongo.MongoClient()[config["mongo_collection"]]

@app.route("/")
def test():
	return render_template("index.html")

@app.route("/new_search", methods=["POST"])
def searchAddRoute():
	mongoConn().searches.insert_one({
			"subreddit": request.form['subreddit'],
			"search_text": request.form['search_text'],
			"last_updated": datetime.now()
			"new": True
		})
	return jsonify({"msg": "Your search has been added to the monitoring list, and will be processed within five minutes."})

@app.route("/search", methods=["POST"])
def searchRoute():
	search_results = searchingInfra.search(ix, request.form['query'])
	return jsonify(search_results)

if __name__ == "__main__":
	#periodicUpdate.backgroundThread()
	app.run()
	
