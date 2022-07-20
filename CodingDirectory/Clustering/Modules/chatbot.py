#self.get_df_from_query(query, max_elems=query_max_elems)
#self.process_df_col(,

import pandas as pd
import numpy as np
from Modules.chatbot_interface import ChatbotInterface

import Modules.solrhandler as sh
import Modules.clusterer as cls
import Modules.topicdeterminator as td
import Modules.chatbot as cb

class Chatbot(ChatbotInterface):

    def __init__(self, initial_query, maxResultSetSize, solrhandler = sh.SolrHandler, clusterer = cls.Clusterer, topicdeterminator = td.TopicDeterminator, forceClusters = False):
        # Komponenten
        self.solrhandler = solrhandler()
        self.clusterer = clusterer()
        self.topicdeterminator = topicdeterminator()
        
        
        #Parameter
        self.forceClusters = forceClusters
        self.maxResultSetSize = maxResultSetSize
        self.decisionTrace = {}
        
        self.query = None
        self.df: pd.DataFrame

        #self.topicBlacklist = []

        #self.nrow = None

        self.df_clus : pd.DataFrame
            
        self.initialQuery(initial_query)


    def initialQuery(self,query):
        self.query = query
        self.df = self.solrhandler.get_df_from_query(query)
        self.df = self.clusterer.run(self.df)

        #self.df = self.topicdeterminator.run(self.df)
        result = self.topicdeterminator.run(self.df)
        self.df = result[0]
        self.df_clus = result[1].sort_values(by = "count", ascending=False) # TODO sekundärer sort nach index

    def recluster(self):
        self.df = self.clusterer.run(self.df, False)
        if self.forceClusters:
            self.findEps()
            
        self.df, self.df_clus = self.topicdeterminator.run(self.df)
        
        self.df_clus = self.df_clus.sort_values(by = "count", ascending=False)
        
    def findEps(self):
        while True:
            
            clusters = self.df[self.clusterer.getClusteredColumn()].values
            if len(np.unique(clusters)) != 1 or self.isFinished():
                break
            else:
                #print(clusters)
                self.clusterer.clustering_algorithm.eps = self.clusterer.clustering_algorithm.eps*0.9
                print(self.clusterer.clustering_algorithm.eps)
                self.recluster()
        
    def refineResultset(self, answer, recluster = False):
        """
        :param clusterId:
        :param answer: True = yes, False = no
        :return: True if finished, False if not
        """

        # go into cluster if topic fits intent or discard cluster, if not
        if answer:
            for topic_component in self.getSelectedTopicForQuestion():
                self.decisionTrace.update({topic_component:True})
            self.df = self.df.loc[self.df[self.clusterer.getClusteredColumn()] == self.getSelectedClusterForQuestion()]#.reset_index()
            self.df_clus = self.df_clus.loc[
                self.df_clus[self.clusterer.getClusteredColumn()] == self.getSelectedClusterForQuestion()]  # .reset_index()
        else:
            for topic_component in self.getSelectedTopicForQuestion():
                self.decisionTrace.update({topic_component:False})
            self.df = self.df.loc[self.df[self.clusterer.getClusteredColumn()] != self.getSelectedClusterForQuestion()]#.reset_index()
            self.df_clus = self.df_clus.loc[
                self.df_clus[self.clusterer.getClusteredColumn()] != self.getSelectedClusterForQuestion()]  # .reset_index()

        # TODO Reclustering und Topic Determination
        #if recluster:
        self.recluster()

    def isFinished(self):
        # return true if finished
#         n_row_bef = len(self.df.index)
#         n_row_aft = len(self.df.index)
        
#         self.is_finished = self.checkFinished(n_row_bef, n_row_aft)
#                 return nrow_aft == nrow_bef or nrow_aft == 1 or nrow_aft == 0 or 
#         if self.is_finished:
#             return True
#         else:
#             return False
        self.isfinished = self.df.shape[0] <= self.maxResultSetSize #len(np.unique(self.df[self.clusterer.getClusteredColumn()].values)) == 1 or
        return self.isfinished
        
    def getSelectedClusterForQuestion(self):
        """

        :return: Cluster with most services
        """
        return self.df_clus[self.clusterer.getClusteredColumn()].values[0]

    def getSelectedTopicForQuestion(self):
        """

        :return:
        """
        return self.df_clus["Topics"].values[0]
    
    def generateQuestion(self):
        """

        :return:
        """
        return "Geht es bei ihrem Anliegen um " + str(self.getSelectedTopicForQuestion()[0])+ "?"
    
    def get_result_string(self) -> str:
        return self.df[["d115Url", "d115Name"]].to_string()
    
    def get_result_html(self) -> str:    
        return "<ul> "+ " ".join(["<li>" + desc + "</li><hr style='height:2px;border-width:0;color:black;background-color:black'>" for desc in self.df["d115Description"]]) + " </ul>"
    
    def add_query(self, query: str):
        if query not in self.query:
            self.initialQuery(self.query + " " + query)
            while sum([~self.decisionTrace.get(topic, True) for topic in self.df_clus["Topics"].values]):
                self.df = self.df.loc[self.decisionTrace.get(topic, True)]
                self.refine()