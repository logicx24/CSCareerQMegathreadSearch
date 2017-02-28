import schedule
import time 
import threading
import logging

import commentFinder
import searchingInfra

#logging.basicConfig(filename='app.log',level=logging.DEBUG)

def handleErrors(job_func):
	def wrapper(*args, **kwargs):
		try:
			job_func(*args, **kwargs)
		except Exception as e:
			logging.debug("Error in periodic update: \n" + str(e))
	return wrapper

@handleErrors
def update():
	logging.info("Starting update.")
	commentFinder.main()
	logging.info("Found comments.")
	searchingInfra.buildIndex()
	logging.info("Updated Index")

@handleErrors
def test():
	logging.info("In a gradually heating bathtub you'll be boiled to death before you know it")
	raise Exception("Everything is cool once you're part of a team")

def backgroundThread():
	schedule.every().day.at("12:00").do(update)
	#schedule.every(5).minutes.do(update)
	kill_update = threading.Event()

	class SearchUpdateThread(threading.Thread):
		def run(self):
			while not kill_update.is_set():
				schedule.run_pending()
				time.sleep(1*60*60) #Every hour. 

	searchThread = SearchUpdateThread()
	searchThread.setDaemon(True)
	searchThread.start()


