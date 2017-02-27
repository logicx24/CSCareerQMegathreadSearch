import praw
import pymongo
from datetime import datetime
from config_dict import config

def setup():
	return praw.Reddit(client_id=config['client_id'],
					   client_secret=config['client_secret'],
					   user_agent=config['user_agent']
					)

def mongoConn():
	return pymongo.MongoClient()[config["mongo_collection"]]

def getAllThreads(reddit, mongoClient):
	found_threads = list(reddit.subreddit("cscareerquestions").search("Automoderator Big 4 Discussion", sort="new"))
	crawled_threads = [crawled for crawled in mongoClient.threads.find({})]

	link_to_last_update = {crawled['link']: crawled['last_crawled'] for crawled in crawled_threads}

	first_time = [
					found for found in found_threads 
					if found.permalink not in link_to_last_update
				]

	mongoClient.threads.insert_many([
		{
			"link": found.permalink,
			"last_crawled": datetime.now()
		}
		for found in first_time
	])

	now = datetime.now()
	needs_update = [
						found for found in found_threads 
						if found.permalink in link_to_last_update 
						and link_to_last_update[found.permalink] < (now - datetime.timedelta(hours=1))
					]

	mongoClient.threads.update_many(
		{
			"link": {
				"$in": [to_update['link'] for to_update in needs_update]
			}
		},
		{
			"$set": {
				"last_crawled": now
			}
		}
	)

	return first_time + needs_update

def getAllComments(threads, mongoClient):
	for thread in threads:
		comments_for_thread = []
		thread.comments.replace_more(limit=0)
		mongoClient.comments.delete_many({
			"thread_link": thread.permalink
		})
		for comment in thread.comments.list():
			comments_for_thread.append({
					"body": comment.body,
					"link": comment.permalink(),
					"indexed": False,
					"thread_link": thread.permalink
				})
		mongoClient.comments.insert_many(comments_for_thread)

def main():
	reddit = setup()
	mongoCli = mongoConn()
	threads = list(getAllThreads(reddit, mongoCli))
	if len(threads) > 0:
		getAllComments(threads, mongoCli)
	else:
		print("No new threads")

if __name__ == "__main__":
	main()
