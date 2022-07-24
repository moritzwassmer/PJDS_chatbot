#!/usr/bin/env python
# coding: utf-8




from keyword_helper import  *
import spacy
import re
import numpy as np
nlp = spacy.load('de_core_news_lg')
from sklearn.feature_extraction.text import CountVectorizer
from chatbot_interface import ChatbotInterface

import solrhandler as sh
import clusterer as cls
import topicdeterminator as td

class Keyword_check(ChatbotInterface):
    def __init__(self,initial_query, maxResultSetSize, solrhandler = sh.SolrHandler, clusterer = cls.Clusterer, topicdeterminator = td.TopicDeterminator,cluster_keywords=False,eps_param=0.2):
        #Pass Paramters
        self.keywords_clustering=cluster_keywords
        self.max_result_length=maxResultSetSize
        self.initial_query=initial_query
        self.nlp= spacy.load('de_core_news_lg')
        self.epsilon=eps_param
        #Init Variables
        self.df= None
        self.words= None
        self.word_occ= None
        self.word_freq= None
        self.current_KW_index=None
        #open classes
        nlp = spacy.load('de_core_news_lg')
        self.solrhandler = solrhandler()
        self.clusterer = clusterer(nlp)
        #
        self.initial_conversation(initial_query)

    def initial_conversation(self, query,col_name="ssdsLemma",result_list_length=3):
        """

        :param query: initial user query
        :param col_name: which column to use
        :param result_list_length: maximum feasible resultset len
        :return: the DF, the occurences, the frequencies, word list and the current asked-about KW
        """
        #initial query & first keyword
        self.query_init_keywords(query, col_name)
        self.max_result_length=result_list_length
        if (len(self.df)==0):
            raise Exception("Empty query result!")
        if col_name not in self.df:
            raise Exception("Column Name not in query result")
        self.init_vector(self.df,col_name)
        self.current_KW_index=choose_question(len(self.word_occ),self.word_freq)
        return self.df,self.word_occ,self.word_freq,self.words,self.current_KW_index

    def refineResultset(self,answer):
        """
        :param answer: Yes:1 or No:0
        :return: true if answer was 1/0/ja/nein
        """
        if answer == "ja" or answer == 1:
            choice=1
        elif answer == "nein" or answer == 0:
            choice=0
        else:
            return False
        #in DF & occurence
        # drops all rows(service) which KW_occurence doesn't match the answer
        self.df=self.df.drop(self.df.index[np.where(self.word_occ[:,self.current_KW_index]!=choice)]).reset_index(drop=True)
        self.word_occ=self.word_occ[np.where(self.word_occ[:,self.current_KW_index]==choice)]
        #recalculates frequencies
        self.word_freq=self.word_occ.sum(axis=0).tolist()
        return True

    def generateQuestion(self):
        """
        :return: question about KW
        """
        #calls function to choose info_gain maximizing KW
        self.current_KW_index = choose_question(len(self.word_occ), self.word_freq)
        #gets that KW
        topic=self.words[self.current_KW_index]
        #generates the question with it
        question=("Geht es bei ihrem anliegen um "+ topic + " ?")
        return question

    def isFinished(self):
        """

        :return: true max result len reached, Flase if else
        """
        if (len(self.word_occ) <= self.max_result_length):
            return True
        else:
            return False

    def get_result_string(self):
        """
        :return: returns string list of current resultset
        """
        result_string = self.df["d115Name"].apply(lambda x: ''.join(x))
        return result_string

    def get_result_html(self):
        result_string = self.df["d115Name"].apply(lambda x: ''.join(x))
        return result_string

    def query_init_keywords(self,query, col_name="ssdsLemma", number=900):
        """

        :param query: user query
        :param col_name: to be clustered by
        :param number: max_number of services
        :return: False if exception, True else
        """

        df = self.solrhandler.get_df_from_query(query)
        #to raise exception instead of error - checks before preprocessing
        if (len(df) == 0):
            raise Exception("Empty query result!")
            return False
        if col_name not in df:
            raise Exception("Column Name not in query result")
            return False
        #
        self.df = process_df_col(df, col_name, nlp)
        if (self.keywords_clustering==True):
            lemma_lst = self.df[f"{col_name}_processed"]
            self.df["nonclustered_lemmas"]=self.df[f"{col_name}_processed"]
            #preprocess every services's keyvalue seperately
            lemma_lst = [preprocess_text(lemma_str, nlp) for lemma_str in lemma_lst]
            #cluster
            topics_lst = get_keywords_clustered(lemma_lst,self.nlp,self.epsilon)
            topics_lst = [" ".join(lst) for lst in topics_lst]
            i=0
            #append topics & original keywords together
            while (i<len(lemma_lst)):
                lemma_lst[i]+=topics_lst[i]
                i+=1

            self.df[f"{col_name}_processed"]=lemma_lst

        return True



    def init_vector(self,df, col_name="ssdsLemma"):
        # initiates the word-occurence & frequency vector and list of words
        vectorizer = CountVectorizer()
        # counts occurences
        a = vectorizer.fit_transform(df[f"{col_name}_processed"]).toarray()
        # boolean of weither or nor a bigger than 0
        b = a > 0
        # bool to int
        self.word_occ = b.astype(int)
        # collect all words
        self.words = vectorizer.get_feature_names()
        # sums word frequencie
        self.word_freq = self.word_occ.sum(axis=0).tolist()

    def next_question(self):
        """
        NOT USED IN ACTUAL CHATBO
        :return: question or resultset
        """
        # Returns ID of next question or list of services if 2 or less
        if (len(self.word_occ) <= self.max_result_length):
            return self.df["d115Name"]
        self.current_KW_index = choose_question(len(self.word_occ), self.word_freq)

        return self.current_KW_index

