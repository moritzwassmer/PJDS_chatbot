#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# -*- coding: utf-8 -*-
"""
Created on Mon May 23 15:26:10 2022

@author: D073079
"""

import pandas as pd

import numpy as np
import scipy
from sklearn.feature_extraction.text import TfidfVectorizer
from operator import itemgetter
from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential

class TopicDeterminator:
    
    def __init__(self):
        self.df_clus= None
        self.df = None
        self.client = None
        
    def run(self, df, top_n=1, clustered_by="ssdsLemma",categorize_key="False"):        
        
        """
            Takes the Dataframe from Clustering, and returns, enriched by the
            topics of the clusters
            Parameter:     
                df Dataframe in format from clustering
                top_n Number of TOpics (from TfIdf) thats sent back
                clustered_by column by which was clustered in clustering
                categorized_key if "False", doesnt use categorizing, otherwise set the key
            Return:
                df + 
                "Topics"(List of words best describing cluster (after Tfidf))
                "categorized" Per Array List of (Word, Category, Score, Offset)
            
        """
        self.df= None
        self.df_clus=None
        self.client = None
        self.df=df
        self.group_by_cluster(clustered_by)
        self.return_topics(top_n,clustered_by)
        if(categorize_key!="False"):            
            self.categorize_text(key=categorize_key,endpoint="https://berlinbobbi.cognitiveservices.azure.com/",col_name="ssdsLemma")
        self.topics_to_service(clustered_by)
        return self.df
        
    def group_by_cluster(self,col_name="ssdsLemma"):
        df_work2 = self.df[[f"{col_name}_processed",f"{col_name}_cluster"]]
        df_work3=df_work2.groupby([f"{col_name}_cluster"])[f"{col_name}_processed"].apply(lambda x: ' '.join(x)).reset_index() 
        df_work2=df_work2.groupby([f"{col_name}_cluster"])[f"{col_name}_processed"].agg('count').to_frame('c').reset_index()
        df_work3['count']=df_work2['c']
        self.df_clus=df_work3
    
    def return_topics(self,n=1,col_name="ssdsLemma"):
        vectorizer=TfidfVectorizer()
        rows = vectorizer.fit_transform(self.df_clus[f"{col_name}_processed"].tolist()).toarray()
        features=vectorizer.get_feature_names()
        i=0
        topics=[]
        while i<len(rows):
            top_feats=[]
            topn_ids = np.argsort(rows[i])[::-1][:n]
            top_feats = [(features[j]) for j in topn_ids]
            topics.append(top_feats)
            i+=1
        self.df_clus['Topics']=topics        
    
    def topics_to_service(self,col_name="ssdsLemma"):
        self.df["Topics"]=self.df.apply(lambda row: self.df_clus.iloc[self.df[f"{col_name}_cluster"].iloc[row.name],2], axis=1)
        if 'categorized' in self.df_clus:
            self.df["categorized"]=self.df.apply(lambda row: self.df_clus.iloc[self.df[f"{col_name}_cluster"].iloc[row.name],3], axis=1)
        
    def authenticate_azure_client(self,key,endpoint="https://berlinbobbi.cognitiveservices.azure.com/"):
        ta_credential = AzureKeyCredential(key)
        text_analytics_client = TextAnalyticsClient(endpoint=endpoint, 
        credential=ta_credential)
        self.client = text_analytics_client   
    
    def categorize_text(self,key,endpoint="https://berlinbobbi.cognitiveservices.azure.com/",col_name="ssdsLemma"):
        self.authenticate_azure_client(key,endpoint)        
        topic=[None]*len(self.df_clus)
        i=0
        while i<len(self.df_clus):            
            documents=[self.df_clus[f"{col_name}_processed"].iloc[i][0:5119]]    
            result =self.client.recognize_entities(documents)[0]
            summary=[]       
            for entity in result.entities:
                categorized=[entity.text,entity.category,round(entity.confidence_score,2),entity.offset]
                summary.append(categorized)
            topic[i]=(sorted(summary,key=itemgetter(3),reverse=False))
            i+=1
        self.df_clus['categorized']=topic
                         
                   
    
    

