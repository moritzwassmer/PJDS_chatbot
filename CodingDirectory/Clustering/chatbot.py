#self.get_df_from_query(query, max_elems=query_max_elems)
#self.process_df_col(,

import pandas as pd

import solrhandler
import clusterer as cls
import topicdeterminator

class Chatbot:

    def __init__(self, solrhandler, clusterer, topicdeterminator):
        self.query = None
        self.solrhandler = solrhandler
        self.clusterer = clusterer
        self.topicdeterminator = topicdeterminator
        self.df = None

    def initialQuery(self,query):
        self.query = query
        self.df = self.solrhandler.get_df_from_query(query)
        self.df = self.clusterer.run(self.df)
        self.df = self.tpc_dterminator.run(self.df)

    def refineCluster(self):

