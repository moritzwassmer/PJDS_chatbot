#!/usr/bin/env python
# coding: utf-8





import spacy
import re
import numpy as np

from sklearn.feature_extraction.text import CountVectorizer
nlp = spacy.load('de_core_news_lg')
#clustering = Clusterer(nlp)
from chatbot_interface import ChatbotInterface

"""
def process_df_col_keywords(df, nlp, col_name="ssdsLemma", do_preprocessing=True):
    #preprocesses
    values = df[col_name]
    if isinstance(values[0], list):
        values = [" ".join(val) for val in values]
    values = [clean_text(val, nlp) for val in values]
    if do_preprocessing:
        values = [preprocess_text(val, nlp) for val in values]
    df[f"{col_name}_processed"] = values
    return df
"""

"""
def query_init_keywords(query, col_name="ssdsLemma", number=900):
    #calls SOLR & preprocessing
    json_file=get_json_from_solr(query,number)
    df=get_df_from_json(json_file)
    if (len(df) == 0):
        raise Exception("Empty query result!")
        return False
    if col_name not in df:
        raise Exception("Column Name not in query result")
        return False
    df_pre=process_df_col(df, col_name,nlp)
    return df_pre
"""

def init_vector_ext(df,col_name="ssdsLemma"):
    #initiates the word-occurence & frequency vector and list of words
    vectorizer = CountVectorizer()
    a = vectorizer.fit_transform(df[f"{col_name}_processed"]).toarray()
    b = a > 0
    word_occ = b.astype(int)
    words = vectorizer.get_feature_names()
    word_freq=word_occ.sum(axis=0).tolist()    
    return word_occ, words, word_freq

def choose_question(length: object, word_freq: object) -> object:
    #Chooses Index of Keywords with occurs closest to 50%
    distance_matrix=[(length/2 - y)**2 for y in word_freq]
    tmp = min(distance_matrix)
    index = distance_matrix.index(tmp)
    return index

def clean_text(text, nlp_model):
    text = re.sub("<[^<]+?>", " ", text)
    text = text.replace("\n", " ")
    text = " ".join(text.split())
    text = " ".join([tok.lower_ for tok in nlp_model(text) if not tok.is_punct])
    return text

def preprocess_text(text, nlp_model):
    doc = nlp_model(text)
    text = " ".join([tok.lemma_ for tok in doc if not tok.is_stop])
    return text.lower()

def process_df_col(df, column, do_preprocessing=True, nlp_model= spacy.load('de_core_news_lg')):
    values = df[column].tolist()
    if isinstance(values[0], list):
        values = [" ".join(val) for val in values]
    values = [clean_text(val, nlp_model) for val in values]
    if do_preprocessing:
        values = [preprocess_text(val, nlp_model) for val in values]
    df[f"{column}_processed"] = values # TODO .loc
    return df

"""
def choose_n_questions(length,word_freq,n):
    #Chooses top n keywords NOT WORKING
    distance_matrix=[(length/2 - y)**2 for y in word_freq]
    sorted_distance=distance_matrix.sort()
    #tmp=sorted_distance[]
    index = distance_matrix.index(tmp)
    return index
"""
def refrain_results_ext(df,word_occ,word_freq,kw_index,choice):
    #returns updated word_occurence, frequency and dataframe to EXTERNAL
    df=df.drop(df.index[np.where(word_occ[:,kw_index]!=choice)]).reset_index(drop=True)
    word_occ=word_occ[np.where(word_occ[:,kw_index]==choice)]
    word_freq=word_occ.sum(axis=0).tolist()
    return df,word_occ,word_freq

def iterate_through_all_keys(df_big,occ_big,freq_big,words_big,result_list_len=6):
    #iterates through all keywords
    #forming sub-DF with every keyword once as initial query
    #in each step runs "iterate_through_all_services"
    i=0
    conversationtime=[]
    while i<len(words_big):
        df,occ,freq=refrain_results_ext(df_big,occ_big,freq_big,i,1)
        j=0
        df_iter=iterate_through_all_services(df,occ,freq,result_list_len)
        i+=1
        conversationtime.append(df_iter["Conversations_needed"].mean())
    return conversationtime

def iterate_through_all_services(df,word_occ_big,word_freq_big,result_list_len=6):
    #iterates through all services in df
    #sets each one as target once and conversates with the backend of chatbot
    #gives back DF enriched by number of conversations (user feedback) it took to get to it
    df_give=df.copy()
    service=0
    conversation_time=[]
    while service<len(df_give):

        service_keys=word_occ_big[service,:]
        index=0
        j=0
        word_freq=word_freq_big
        word_occ=word_occ_big
        df=df_give.copy()
        while len(df)>result_list_len:
            index=choose_question(len(df),word_freq)
            choice=(service_keys[index])                
           
            df,word_occ,word_freq=refrain_results_ext(df,word_occ,word_freq,index,choice)
            j+=1               
        conversation_time.append(j)
        service+=1
    df_give["Conversations_needed"]=conversation_time
    return df_give

class Keyword_check(ChatbotInterface):
    def __init__(self,solrhandler,clusterer,topic_dterminator,initial_query,maxResultSetSize,cluster_keywords=False):
        #Paramters
        self.keywords_clustering=cluster_keywords
        self.max_result_length=maxResultSetSize
        self.initial_query=initial_query
        #Init
        self.df= None
        self.words= None
        self.word_occ= None
        self.word_freq= None
        self.result_length= None
        self.current_KW_index=None
        #open classes
        nlp = spacy.load('de_core_news_lg')
        self.solrhandler = solrhandler()
        self.clusterer = clusterer(nlp)
        self.initial_conversation(initial_query)



            
    def initial_conversation(self, query,col_name="ssdsLemma",result_list_length=3):
        #initial query & first keyword
        self.query_init_keywords(query, col_name)
        self.max_result_length=result_list_length
        if (len(self.df)==0):
            raise Exception("Empty query result!")
            return self.df,self.word_occ,self.word_freq,self.words,index
        if col_name not in self.df:
            raise Exception("Column Name not in query result")
        self.init_vector(self.df,col_name)
        self.current_KW_index=choose_question(len(self.word_occ),self.word_freq)
        return self.df,self.word_occ,self.word_freq,self.words,self.current_KW_index

    def refineResultset(self,answer):
        #updates the word_occurence, frequency and underlying dataframe
        #Return False if answer was neither ja nor nein

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
        if (len(self.word_occ) <= self.result_length):
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

