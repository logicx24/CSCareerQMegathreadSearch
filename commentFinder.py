import praw
import pymongo
from datetime import datetime, timedelta
from config_dict import config

from urlparse import urlparse

def setup():
	return praw.Reddit(client_id=config['client_id'],
					   client_secret=config['client_secret'],
					   user_agent=config['user_agent']
					)

def mongoConn():
	return pymongo.MongoClient()[config["mongo_collection"]]

def updateCurrentThreads(reddit):
	if is_link:
		return [reddit.submission(url=args[0])]
	else:
		return list(reddit.subreddit(args[0]).search(args[1]))

def getSearchUpdateThreads(reddit, mongoClient):
	#found_threads = list(reddit.subreddit("cscareerquestions").search("Automoderator Big 4 Discussion", sort="new"))
	now = datetime.now()

	searches_to_update = [
							tmp for tmp in mongoClient.searches.find({}) 
							if tmp['new'] 
							or tmp['last_updated'] <= (now - timedelta(hours=1))
						]

	mongoClient.searches.update_many(
		{
			"_id": {
				"$in": [search_to_update['_id'] for search_to_update in searches_to_update]
			}
		},
		{
			"$set": {
				"last_updated": now,
				"new": False
			}
		}
	)

	found_threads = []
	for tagged_search in searches_to_update:
		found_threads += [
							(thread, tagged_search) for thread in
							reddit.subreddit(tagged_search['subreddit']).search(tagged_search['search_text'], sort="new")
						]

	crawled_threads = [crawled for crawled in mongoClient.threads.find({})]

	link_to_last_update = {crawled['link']: crawled['last_crawled'] for crawled in crawled_threads}

	first_time = [
					found for found in found_threads 
					if found[0].permalink not in link_to_last_update
				]
	
	if len(first_time) > 0:
		inserted_ids = mongoClient.threads.insert_many([
			{
				"link": urlparse(found[0].permalink).path,
				"last_crawled": now,
				"new": False,
				"parent_search_id": found[1]["_id"]
			}
			for found in first_time
		])
		mongoClient.threads.find_many({})

		return first_time #+ needs_update
	else:
		return []

def getThreadsUpdate(reddit, mongoClient):
	crawled_threads = [crawled for crawled in mongoClient.threads.find({})]
	now = datetime.now()
	needs_update = [
					crawled for crawled in crawled_threads 
					if crawled['last_crawled'] < (now - timedelta(hours=1))
					or crawled['new']
				]
	if len(needs_update) > 0:
		mongoClient.threads.update_many(
			{
				"link": {
					"$in": [to_update["link"] for to_update in needs_update]
				}
			},
			{
				"$set": {
					"last_crawled": now,
					"new": False
				}
			}
		)
	return [(reddit.submission(url="https://reddit.com" + thread['link']), thread) for thread in needs_update]

def getAllComments(threads, mongoClient):
	for thread, db_thread in threads:
		comments_for_thread = []
		thread.comments.replace_more(limit=0)
		mongoClient.comments.delete_many({
			"thread_link": thread.permalink
		})
		for comment in thread.comments.list():
			comments_for_thread.append({
					"body": comment.body,
					"link": urlparse(comment.permalink()).path,
					"indexed": False,
					"thread_link": db_thread['link'],
					"karma": comment.score,
					"time_posted": datetime.fromtimestamp(comment.created),
					"parent_thread_id": db_thread["_id"]
				})
		mongoClient.comments.insert_many(comments_for_thread)

def main():
	reddit = setup()
	mongoCli = mongoConn()
	#threads = list(getAllThreads(reddit, mongoCli))
	threads = getThreadsUpdate(reddit, mongoCli) + getSearchUpdateThreads(reddit, mongoCli)
	if len(threads) > 0:
		getAllComments(threads, mongoCli)
	else:
		print("No new threads")

if __name__ == "__main__":
	main()
