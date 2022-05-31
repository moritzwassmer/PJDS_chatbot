#!/usr/bin/env python
# coding: utf-8





import spacy
import numpy as np

from clusterer import Clusterer
#import clusterer
from clusterer import clean_text, process_df_col
from solrhandler import get_json_from_solr, get_df_from_json
from sklearn.feature_extraction.text import CountVectorizer
nlp = spacy.load('de_core_news_lg')
clustering = Clusterer(nlp)


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
def query_init_keywords(query, col_name="ssdsLemma", number=900):
    #calls SOLR & preprocessing
    json_file=get_json_from_solr(query,number)
    df=get_df_from_json(json_file)
    df_pre=process_df_col(df, col_name,nlp)
    return df_pre

def init_vector(df,col_name="ssdsLemma"):
    #initiates the word-occurence & frequency vector
    vectorizer = CountVectorizer()
    a = vectorizer.fit_transform(df[f"{col_name}_processed"]).toarray()
    b = a > 0
    word_occ = b.astype(int)
    words = vectorizer.get_feature_names()
    word_freq=word_occ.sum(axis=0).tolist()    
    return word_occ, words, word_freq

def choose_question(length,word_freq):
    #Chooses Keywords with occurs closest to 50%
    distance_matrix=[(length/2 - y)**2 for y in word_freq]
    #sq_distance_matrix=np.square(distance_matrix)
    tmp = min(distance_matrix)
    index = distance_matrix.index(tmp)
    return index  

def refrain_results_ext(df,word_occ,word_freq,kw_index,choice):
    #updates the word_occurence, frequency and underlying dataframe to EXTERNAL
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
        print(i)
    return conversationtime

def iterate_through_all_services(df,word_occ_big,word_freq_big,result_list_len=6):
    #iterates through all services in df
    #sets each one as target once and conversates with the backend of chatbot
    #gives back DF enriched by number of conversations (user feedback) it took to get to it
    df_give=df.copy()
    service=0
    conversation_time=[]
    while service<len(df_give):
        print(conversation_time)
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



class Keyword_check:
    def __init__(self):
        self.df= None
        self.words= None
        self.word_occ= None
        self.word_freq= None
        self.result_length= None
            
    def initial_conversation(self, query,col_name="ssdsLemma",result_list_length=2):
        #initial query & first keyword
        self.df = query_init_keywords(query, col_name)
        self.result_length=result_list_length
        if (len(self.df)==0):
            print("Empty query result!")
            return self.df,self.word_occ,self.word_freq,self.words,index
        self.word_occ,self.words,self.word_freq=init_vector(self.df,col_name)            
        index=choose_question(len(self.word_occ),self.word_freq)      
        return self.df,self.word_occ,self.word_freq,self.words,index
    
    def refrain_results(self,kw_index,choice):
        #updates the word_occurence, frequency and underlying dataframe
        self.df=self.df.drop(self.df.index[np.where(self.word_occ[:,kw_index]!=choice)]).reset_index(drop=True)
        self.word_occ=self.word_occ[np.where(self.word_occ[:,kw_index]==choice)]
        self.word_freq=self.word_occ.sum(axis=0).tolist()
        
    def next_question(self):
        #Returns ID of next question or list of services if 2 or less
        if(len(self.word_occ)<=self.result_length):
            return self.df["d115Name"]
        index=choose_question(len(self.word_occ),self.word_freq)        
        return index
    
    
