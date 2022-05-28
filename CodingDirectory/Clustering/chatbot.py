#self.get_df_from_query(query, max_elems=query_max_elems)
#self.process_df_col(,

import pandas as pd

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

        self.topicBlacklist = []

        self.nrow = None


    def initialQuery(self,query):
        self.query = query
        self.df = self.solrhandler.get_df_from_query(query)
        self.df = self.clusterer.run(self.df)
        self.df = self.tpc_dterminator.run(self.df)[0]


    def findCorrectAnswer(self,targetService):
        """
        :return: True: targetService is in Cluster which is to be asked about False: else
        """

        # Find Target Cluster
        temp = self.tpc_dterminator.df
        clusteredColumn = self.clusterer.getClusteredColumn()
        service = temp.loc[temp["id"]==str(targetService)]
        targetCluster = service[clusteredColumn][0]

        if targetCluster == self.getSelectedClusterForQuestion():
            return True
        else:
            return False

    def refineResultset(self, answer): # TODO Silvio
        """
        :param clusterId:
        :param answer: True = yes, False = no
        :return:
        """

        #self.topicBlacklist = self.topicBlacklist + [self.getSelectedTopicForQuestion()] # Append topic to blacklist

        n_row_bef = len(self.df.index)
        # go into cluster if topic fits intent or discard cluster, if not
        if answer:
            self.df = self.df.loc[self.df[self.clusterer.getClusteredColumn()] == self.getSelectedClusterForQuestion()]
        else:
            self.df = self.df.loc[self.df[self.clusterer.getClusteredColumn()] != self.getSelectedClusterForQuestion()]
        n_row_aft = len(self.df.index)

        # check if finished
        is_finished = n_row_aft == n_row_bef | n_row_aft == 0

        if is_finished:
            return False
        else:
            return True

        # Refine Cluster + Topics
        self.df = self.clusterer.run(self.df)
        self.df = self.topicdeterminator.run(self.df)

    def getSelectedClusterForQuestion(self): # TODO Silvio
        """

        :return: Cluster with most services
        """
        df_row = self.tpc_dterminator.df_clus.sort_values(by = "count", ascending=False).head(1)
        return df_row[self.clusterer.getClusteredColumn()][0]

    def getSelectedTopicForQuestion(self):
        """

        :return:
        """
        df_row = self.tpc_dterminator.df_clus.sort_values(by="count", ascending=False).head(1)

        return df_row["Topics"][0]

    def generateQuestion(self):
        """

        :return:
        """
        return "Geht es bei ihrem Anliegen um " + self.getSelectedTopicForQuestion()+ "?"