from keyword_check import Keyword_check
import math
import statistics
import numpy as np
import pandas as pd
from keyword_check import *


class Keywords_eval:

    def __init__(self):
        self.keywords=Keyword_check()
        self.df= None
        self.df_logs = None
        self.file_list=[]
        self.dialogId_list=[]
        self.id_list = []
        self.t_list = []
        self.service_name_list=[]
        self.query_list=[]
        self.question_list = []
        self.answer_list = []
        self.rank_list = []
        self.nResults_list = []





    def initialize_evaluation(self,df,result_list=2):
        """
        :param df: dataframe in format of moritz dataset of original queries
        :param result_list_len: optional param to specify at what No of results to stop

        :return: return log DF
        """
        self.df = df
        self.test_dataset_2_keyword(df,result_list)
        self.conclude_logs()
        return self.df_logs

    def test_dataset_2_keyword(self,df, result_list_len=3):
        """
        :param df: dataframe in format of moritz dataset of original queries
        :param result_list_len: optional param to specify at what No of results to stop
        :return: none
        """
        #i = counter over initial query
        i = 0
        while i < len(df):

            print(i)
            try:
                #fetches params for specific query
                df_query, occ_query, freq_query, words_query, index = self.keywords.initial_conversation(query=df["initialQuestion"].iloc[i],col_name="ssdsLemma",result_list_length=result_list_len)
                a = df_query["id"] == str(df["documentId"].iloc[i])
            except Exception as e:
                if (str(e) == 'response'):
                    self.skip_one_row(i)
                    next
                else:
                    print(e)

            if len(a[a]) == 0:
                i += 1
            else:
                #stores copy of targeted service's word occurences
                service_keys = occ_query[a][0]
                #t = counter over conversation turns
                t = 0
                #index will be type(list) if questioning resulted in final suggestions
                while type(index) is int:

                    choice = (service_keys[index])
                    t += 1
                    rank= self.keywords.df[self.keywords.df["id"] == str(df["documentId"].iloc[i])].index.values[0]
                    self.append_val_to_list(i,t,len(self.keywords.word_occ),(rank+1),words_query[index],choice)
                    self.keywords.refrain_results(index, choice)
                    index = self.keywords.next_question()

                i += 1


    def conclude_logs(self):
        """

        :return: summs up all lists into a df of logs
        """

        self.df_logs=pd.DataFrame(list(zip(self.file_list,self.dialogId_list,self.id_list,self.t_list,self.service_name_list,
                                           self.query_list,self.question_list,self.answer_list,self.rank_list,self.nResults_list)),
                                  columns=['file','dialogId','ID','t','name','initialQuestion','question','answer','rank','nResult'])


    def append_val_to_list(self,i,j,nResults,rank,qWord,answer):
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
        self.question_list.append("Geht es bei Ihrem Anliegen um " + qWord + "?")
        self.answer_list.append(bool(answer))
        self.rank_list.append(rank)
        self.nResults_list.append(nResults)




    def skip_one_row(self,i):
        """
        adds None etc. to lists in case exception is thrown
        :param i: iteration of new Queries
        :return:
        """

        self.file_list.append(self.df['file'].iloc[i])
        self.dialogId_list.append(self.df['dialogId'].iloc[i])
        self.id_list.append(i)
        self.t_list.append(0)
        self.service_name_list.append(self.df['name'].iloc[i])
        self.query_list.append(self.df['initialQuestion'].iloc[i])
        self.nResults_list.append(None)
        self.rank_list.append(None)
        self.question_list.append(None)
        self.answer_list.append(None)



