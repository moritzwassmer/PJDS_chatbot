#self.get_df_from_query(query, max_elems=query_max_elems)
#self.process_df_col(,

import pandas as pd
import numpy as np

import solrhandler
import clusterer as cls
import topicdeterminator

class Chatbot:

    def __init__(self, solrhandler, clusterer, topicdeterminator):

        # Komponenten
        self.solrhandler = solrhandler
        self.clusterer = clusterer
        self.topicdeterminator = topicdeterminator

        self.query = None
        self.df: pd.DataFrame

        #self.topicBlacklist = []

        #self.nrow = None

        self.df_clus : pd.DataFrame


    def initialQuery(self,query):
        self.query = query
        self.df = self.solrhandler.get_df_from_query(query)
        self.df = self.clusterer.run(self.df)

        #self.df = self.topicdeterminator.run(self.df)
        result = self.topicdeterminator.run(self.df)
        self.df = result[0]
        self.df_clus = result[1].sort_values(by = "count", ascending=False)


    # TODO in Evaluierung ausgelagert, für Testzwecke in Modul lassen
    def findCorrectAnswer(self,targetService):
        """
        :return: True: targetService is in Cluster which is to be asked about False: else
        """

        # Find Target Cluster
        clusteredColumn = self.clusterer.getClusteredColumn()
        service = self.df.loc[self.df["id"]==str(targetService)]
        if len(service[clusteredColumn].values) == 0:
            raise Exception("Answer not in resultset")

        targetCluster = service[clusteredColumn].values[0]

        if targetCluster == self.getSelectedClusterForQuestion():
            return True

        else:
            return False


    def refineResultset(self, answer):
        """
        :param clusterId:
        :param answer: True = yes, False = no
        :return: True if finished, False if not
        """

        # go into cluster if topic fits intent or discard cluster, if not
        n_row_bef = len(self.df.index)
        if answer:
            self.df = self.df.loc[self.df[self.clusterer.getClusteredColumn()] == self.getSelectedClusterForQuestion()]#.reset_index()
            self.df_clus = self.df_clus.loc[
                self.df_clus[self.clusterer.getClusteredColumn()] == self.getSelectedClusterForQuestion()]  # .reset_index()
        else:
            self.df = self.df.loc[self.df[self.clusterer.getClusteredColumn()] != self.getSelectedClusterForQuestion()]#.reset_index()
            self.df_clus = self.df_clus.loc[
                self.df_clus[self.clusterer.getClusteredColumn()] != self.getSelectedClusterForQuestion()]  # .reset_index()
        n_row_aft = len(self.df.index)

        # return true if finished
        self.is_finished = self.checkFinished(n_row_bef, n_row_aft)
        if self.is_finished:
            return True
        else:
            return False

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

    def checkFinished(self, nrow_bef, nrow_aft):
        return nrow_aft == nrow_bef or nrow_aft == 1 or nrow_aft == 0 or len(np.unique(self.df[self.clusterer.getClusteredColumn()].values)) == 1