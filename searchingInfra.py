
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


def mongoConn():
	return pymongo.MongoClient()[config["mongo_collection"]]

def genIndex():
	schema = Schema(body=TEXT(stored=True), 
					link=ID(stored=True, unique=True),
					karma=NUMERIC(int, 64, stored=True),
					posted_date=DATETIME(stored=True))

	if not os.path.exists("indexdir"):
	    os.mkdir("indexdir")

	if index.exists_in("indexdir"):
		ix = index.open_dir("indexdir")
	else:
		ix = index.create_in("indexdir", schema)

	return ix

def buildIndex(ix):
	mongoCli = mongoConn()
	writer = ix.writer()

	for comment in mongoCli.comments.find({"indexed": False}):
		writer.update_document(
			body=comment['body'],
			link=comment['link'],
			karma=comment['karma'],
			posted_date=comment['time_posted']
		)
	writer.commit()
	mongoCli.comments.update_many({"indexed": False}, {"$set": {"indexed": True}})

def updateIndex():
	return buildIndex(genIndex())

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
	ix = genIndex()
	buildIndex(ix)
	print(search(ix, "jeff bezos"))









