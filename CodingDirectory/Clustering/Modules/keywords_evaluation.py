from keyword_check import Keyword_check
import math
import statistics
import numpy as np
import pandas as pd
from keyword_check import *
from sklearn.cluster import DBSCAN


class Keywords_eval:

    def __init__(self, solrhandler, Keyword_check, query, maxResultSetSize,do_kw_clustering=True,clus_algo=DBSCAN(eps=0.2, min_samples=1, metric="cosine" )):
        #function call, first query call is irrelevant hereby
        self.keywords = Keyword_check(query,maxResultSetSize,solrhandler, do_kw_clustering,clus_algo)
        #variable init
        self.clus_algo=clus_algo
        self.df = None
        self.df_logs = None
        self.file_list = []
        self.dialogId_list = []
        self.id_list = []
        self.t_list = []
        self.service_name_list = []
        self.query_list = []
        self.question_list = []
        self.answer_list = []
        self.rank_list = []
        self.nResults_list = []
        self.max_result_length=maxResultSetSize

    def initialize_evaluation(self, df, result_list=1):
        """
        :param df: dataframe in format of moritz dataset of original queries
        :param result_list: optional param to specify at what No of results to stop

        :return: return log DF
        """
        #fill variable with eval-dataset
        self.df = df
        self.test_dataset_2_keyword(df, result_list)
        self.conclude_logs()
        return self.df_logs

    def test_dataset_2_keyword(self, df, result_list_len=3):
        """
        :param df: dataframe in format of moritz dataset of original queries
        :param result_list_len: optional param to specify at what No of results to stop
        :return: none
        """
        # i = counter over initial query
        i = 0
        while i < len(df):
            try:
                # fetches params for specific query from i-th row of eval-dataset
                df_query, occ_query, freq_query, words_query, index = self.keywords.initial_conversation(
                    query=df["initialQuestion"].iloc[i], col_name="ssdsLemma", result_list_length=self.max_result_length)
                #a is list, if service of resultset matches searched for ground-truth-service from eval-dataset
                a = df_query["id"] == str(df["documentId"].iloc[i])
            except Exception as e:
                if (str(e) == 'response'):
                    self.skip_one_row(i)
                    i += 1
                    continue
                elif (str(e) == 'no solr output'):

                    self.skip_one_row(i)
                    i += 1
                    continue
                else:
                    print(e)
                    self.skip_one_row(i)
                    i += 1
                    continue


            if len(a[a]) == 0:
                #if ==0 this means ground-truth-service is not in query-result
                i += 1
            else:
                # stores copy of targeted service's word occurences
                service_keys = occ_query[a][0]
                # t = counter over conversation turns
                t = 0
                #initial rank of ground truth service
                rank = self.keywords.df[self.keywords.df["id"] == str(df["documentId"].iloc[i])].index.values[0]
                self.append_val_to_list(i, t, len(self.keywords.word_occ), (rank + 1), "initialQuery", None)
                # index will be type(list) if questioning resulted in final suggestions
                while type(index) is int:
                    choice = (service_keys[index])
                    t += 1
                    #based on groud-truth-services KW-occurence refine the resultset
                    self.keywords.refineResultset(choice)
                    rank = self.keywords.df[self.keywords.df["id"] == str(df["documentId"].iloc[i])].index.values[0]
                    self.append_val_to_list(i, t, len(self.keywords.word_occ), (rank + 1),
                                            str("Geht es bei Ihrem Anliegen um " + words_query[index]) + "?", choice)
                    #get next question
                    index = self.keywords.next_question()




                i += 1

    def conclude_logs(self):
        """

        :return: summs up all lists into a df of logs
        """
        self.df_logs = pd.DataFrame(
            list(zip(self.file_list, self.dialogId_list, self.id_list, self.t_list, self.service_name_list,
                     self.query_list, self.question_list, self.answer_list, self.rank_list, self.nResults_list)),
            columns=['file', 'dialogId', 'ID', 't', 'name', 'initialQuestion', 'question', 'answer', 'rank', 'nResult'])

    def append_val_to_list(self, i, j, nResults, rank, qWord, answer):
        """
        adds all logable values to respective lists
        :params: corresponding params for logging
        :return: none
        """
        self.file_list.append(self.df['file'].iloc[i])
        self.dialogId_list.append(self.df['dialogId'].iloc[i])
        self.id_list.append(i)
        self.t_list.append(j)
        self.service_name_list.append(self.df['name'].iloc[i])
        self.query_list.append(self.df['initialQuestion'].iloc[i])
        self.question_list.append(qWord)
        self.answer_list.append(bool(answer))
        self.rank_list.append(rank)
        self.nResults_list.append(nResults)

    def skip_one_row(self, i):
        """
        adds None etc. to lists in case exception is thrown
        :param i: iteration of new Queries
        :return:
        """

        self.file_list.append(self.df['file'].iloc[i])
        self.dialogId_list.append(self.df['dialogId'].iloc[i])
        self.id_list.append(i)
        self.t_list.append(None)
        self.service_name_list.append(self.df['name'].iloc[i])
        self.query_list.append(self.df['initialQuestion'].iloc[i])
        self.nResults_list.append(None)
        self.rank_list.append(None)
        self.question_list.append(None)
        self.answer_list.append(None)
