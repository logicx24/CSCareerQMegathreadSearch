
from config_dict import config

from whoosh import index
from whoosh import sorting
from whoosh.fields import Schema, ID, KEYWORD, TEXT
from whoosh.qparser import QueryParser
from whoosh import writing

import os, os.path
import pymongo

def mongoConn():
	return pymongo.MongoClient()[config["mongo_collection"]]

def genIndex():
	schema = Schema(body=TEXT(stored=True), 
					link=ID(stored=True))

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
		writer.add_document(
			body=comment['body'],
			link=comment['link']
		)
	writer.commit()
	mongoCli.comments.update_many({"indexed": False}, {"$set": {"indexed": True}})

def updateIndex():
	return buildIndex(genIndex())

def clearIndex(ix):
	writer = ix.writer()
	writer.commit(mergetype=writing.CLEAR)
	mongoCli.comments.update_many({"indexed": True}, {"$set": {"indexed": False}})

def search(ix, text):
	with ix.searcher() as searcher:
		qp = QueryParser("body", schema=ix.schema)
		q = qp.parse(text)

		search_hits = searcher.search(q, limit=None, terms=True)

		res = []
		for hit in search_hits:
			tmp = dict(hit)
			tmp['matching_terms'] = [x[1] for x in hit.matched_terms()]
			tmp['highlights'] = hit.highlights("body")
			res.append(tmp)
		res.append([x[1] for x in search_hits.matched_terms()])

	return res

if __name__ == "__main__":
	ix = genIndex()
	buildIndex(ix)
	print(search(ix, "promoted and I work"))









