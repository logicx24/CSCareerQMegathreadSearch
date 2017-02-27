import praw
import pymongo

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
	crawled_perm_set = set(crawled['link'] for crawled in mongoClient.threads.find({}))

	mongoClient.threads.insert_many([
			{"link": found.permalink}
			for found in found_threads
		])

	return [found for found in found_threads if found.permalink not in crawled_perm_set]


def getAllComments(threads, mongoClient):
	for thread in threads:
		comments_for_thread = []
		thread.comments.replace_more(limit=0)
		for comment in thread.comments.list():
			comments_for_thread.append({
					"body": comment.body,
					"link": comment.permalink(),
					"indexed": False
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
	mongoCli.close()

if __name__ == "__main__":
	main()
