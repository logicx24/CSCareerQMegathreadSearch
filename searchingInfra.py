
from config_dict import config

from whoosh import index
from whoosh import sorting
from whoosh import writing

from whoosh.fields import Schema, ID, KEYWORD, TEXT, NUMERIC, DATETIME
from whoosh import highlight
from whoosh.qparser import QueryParser

import os, os.path
import pymongo
import time

schema = Schema(body=TEXT(stored=True), 
				link=ID(stored=True, unique=True),
				karma=NUMERIC(int, 64, stored=True),
				posted_date=DATETIME(stored=True))


def mongoConn():
	return pymongo.MongoClient()[config["mongo_collection"]]

def genIndex(obj, is_search):

	if not os.path.exists("indexdir"):
	    os.mkdir("indexdir")

	# if index.exists_in("indexdir"):
	# 	ix = index.open_dir("indexdir")
	# else:
	# 	ix = index.create_in("indexdir", schema)

	# return ix
	if is_search:
		return genIndexSearch(obj)
	else:
		return genIndexThread(obj)

def genIndexSearch(search_obj):
	iname = search_obj['subreddit'] + search_obj['search_text']
	if index.exists_in("indexdir", indexname=iname):
		ix = index.open_dir("indexdir", indexname=iname)
	else:
		ix = index.create_in("indexdir", schema=schema, indexname=iname)
	return ix

def genIndexThread(thread_obj):
	iname = thread_obj['link']
	if index.exists_in("indexdir", indexname=iname):
		ix = index.open_dir("indexdir", indexname=iname)
	else:
		ix = index.create_in("indexdir", schema=schema, indexname=iname)
	return ix


def buildIndex(ix, obj, is_search):
	# mongoCli = mongoConn()
	# writer = ix.writer()

	# for comment in mongoCli.comments.find({"indexed": False}):
	# 	writer.update_document(
	# 		body=comment['body'],
	# 		link=comment['link'],
	# 		karma=comment['karma'],
	# 		posted_date=comment['time_posted']
	# 	)
	# writer.commit()
	# mongoCli.comments.update_many({"indexed": False}, {"$set": {"indexed": True}})
	if is_search:
		buildIndexSearch(ix, obj)
	else:
		buildIndexThread(ix, obj)

def buildIndexSearch(ix, search_obj):
	mongoCli = mongoConn()
	writer = ix.writer()

	threads = mongoCli.threads.find({"parent_search_id": search_obj["_id"]})
	comments = []
	for thread in threads:
		comments = mongoCli.comments.find({"parent_thread_id": thread["_id"], "indexed": False})
		for comment in comments:
			writer.update_document(
				body=comment['body'],
				link=comment['link'],
				karma=comment['karma'],
				posted_date=comment['time_posted']
			)
		mongoCli.comments.update_many({"indexed": False, "parent_thread_id": thread["_id"]}, {"$set": {"indexed": True}})
	writer.commit()

def buildIndexThread(ix, thread_obj):
	mongoCli = mongoConn()
	writer = ix.writer()

	for comment in mongoCli.comments.find({"parent_thread_id": thread_obj["_id"], "indexed": False}):
		writer.update_document(
			body=comment['body'],
			link=comment['link'],
			karma=comment['karma'],
			posted_date=comment['time_posted']
		)
	writer.commit()
	mongoCli.comments.update_many({"indexed": False}, {"$set": {"indexed": True}})
	

def updateIndex(obj, is_search):
	ix = genIndex(obj, is_search)
	buildIndex(ix, obj, is_search)

def clearIndex(ix):
	mongoCli = mongoConn()
	writer = ix.writer()
	writer.commit(mergetype=writing.CLEAR)
	mongoCli.comments.update_many({"indexed": True}, {"$set": {"indexed": False}})

def search(ix, text):
	with ix.searcher() as searcher:
		qp = QueryParser("body", schema=ix.schema)
		q = qp.parse(text)

		search_hits = searcher.search(q, limit=None, terms=True)
		search_hits.fragmenter = highlight.SentenceFragmenter(maxchars=450)

		res = []
		for hit in search_hits:
			tmp = dict(hit)
			tmp['matching_terms'] = [x[1] for x in hit.matched_terms()]
			tmp['highlights'] = hit.highlights("body")
			res.append(tmp)

	return {"hits": res, "matched_terms": [x[1] for x in search_hits.matched_terms()]}

if __name__ == "__main__":
	# ix = genIndex()
	# buildIndex(ix)
	obj = mongoConn().searches.find_one({"search_text": "Automoderator Big 4 Discussion"})
	ix = genIndex(obj, True)
	buildIndex(ix, obj, True)
	print(search(ix, "jeff bezos"))

	obj = mongoConn().searches.find_one({"search_text": "Automoderator Daily Chat Thread"})
	ix = genIndex(obj, True)
	buildIndex(ix, obj, True)
	print(search(ix, "jeff bezos"))









