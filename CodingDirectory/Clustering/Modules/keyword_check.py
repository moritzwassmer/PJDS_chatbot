#!/usr/bin/env python
# coding: utf-8




from keyword_helper import  *
import spacy
import re
import numpy as np
nlp = spacy.load('de_core_news_lg')
from sklearn.feature_extraction.text import CountVectorizer
from chatbot_interface import ChatbotInterface



class Keyword_check(ChatbotInterface):
    def __init__(self,solrhandler,clusterer,topic_dterminator,initial_query,maxResultSetSize,cluster_keywords=False):
        #Pass Paramters
        self.keywords_clustering=cluster_keywords
        self.max_result_length=maxResultSetSize
        self.initial_query=initial_query
        self.nlp= spacy.load('de_core_news_lg')
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
        :return: true if word occurence & df could be updated
        """
        if answer == "ja" or answer == 1:
            choice=1
        elif answer == "nein" or answer == 0:
            choice=0
        else:
            return False
        self.df=self.df.drop(self.df.index[np.where(self.word_occ[:,self.current_KW_index]!=choice)]).reset_index(drop=True)
        self.word_occ=self.word_occ[np.where(self.word_occ[:,self.current_KW_index]==choice)]
        self.word_freq=self.word_occ.sum(axis=0).tolist()
        return True

    def generateQuestion(self):
        #Returns Question
        self.current_KW_index = choose_question(len(self.word_occ), self.word_freq)
        topic=self.words[self.current_KW_index]
        question=("Geht es bei ihrem anliegen um "+ topic + " ?")
        return question

    def isFinished(self):
        if (len(self.word_occ) <= self.max_result_length):
            return True
        else:
            return False

    def get_result_string(self):
        result_string = self.df["d115Name"].apply(lambda x: ''.join(x))
        return result_string

    def get_result_html(self):
        result_string = self.df["d115Name"].apply(lambda x: ''.join(x))
        return result_string

    def query_init_keywords(self,query, col_name="ssdsLemma", number=900):
        # calls SOLR & preprocessing

        df = self.solrhandler.get_df_from_query(query)
        if (len(df) == 0):
            raise Exception("Empty query result!")
            return False
        if col_name not in df:
            raise Exception("Column Name not in query result")
            return False
        self.df = process_df_col(df, col_name, nlp)
        if (self.keywords_clustering==True):
            #lemma_lst = ["".join(lst) for lst in self.df.ssdsLemma_processed.tolist()]
            lemma_lst = self.df["ssdsLemma_processed"]
            self.df["nonclustered_lemmas"]=self.df[f"{col_name}_processed"]

            lemma_lst = [preprocess_text(lemma_str, nlp) for lemma_str in lemma_lst]

            lemma_lst = get_keywords_clustered(lemma_lst,self.nlp)

            lemma_lst = [" ".join(lst) for lst in lemma_lst]

            self.df[f"{col_name}_processed"]=lemma_lst




    def init_vector(self,df, col_name="ssdsLemma"):
        # initiates the word-occurence & frequency vector and list of words
        vectorizer = CountVectorizer()
        a = vectorizer.fit_transform(df[f"{col_name}_processed"]).toarray()
        b = a > 0
        self.word_occ = b.astype(int)
        self.words = vectorizer.get_feature_names()
        self.word_freq = self.word_occ.sum(axis=0).tolist()

    def next_question(self):
        # Returns ID of next question or list of services if 2 or less
        if (len(self.word_occ) <= self.max_result_length):
            return self.df["d115Name"]
        self.current_KW_index = choose_question(len(self.word_occ), self.word_freq)

        return self.current_KW_index

