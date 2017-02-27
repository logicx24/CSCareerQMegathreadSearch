from flask import Flask
import periodicUpdate
import searchingInfra

app = Flask(__name__)
ix = searchingInfra.genIndex()

@app.route("/")
def test():
	return "hitler had the right ideas with the wrong means"

@app.route("/search", methods=["POST"])
def searchRoute():
	search_results = searchingInfra.search(ix, request.form['query'])
	return search_results

if __name__ == "__main__":
	periodicUpdate.backgroundThread()
	app.run()
	
