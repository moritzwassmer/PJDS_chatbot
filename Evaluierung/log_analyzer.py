import math
import statistics
#import numpy as np
import pandas as pd

class Log_Analyzer():

    def __init__(self,df):
        self.df = df
        self.services=None
        self.questions=None
        self.mean_nResults_reduction=None
        self.harmonic_mean_nResults_reduction=None
        self.mean_delta_nResults=None
        self.mean_delta_Rank=None
        self.mean_Turns=None
        self.ninety_centile_turns=None
        self.threequartile_turns=None
        self.onequartile_turns = None
        self.median_Turns=None
        self.means= {None}
        self.max_turns_needed=None
        self.conversations=None
        self.info_gain_mean=None

    def run_it(self):
        self.add_deltas()
        self.aggregate_services()
        self.aggregate_questions()
        self.means={"Mean Turns":self.mean_Turns,
                    "90-percentile Turns":self.ninety_centile_turns,
                    "75% quantile Turns":self.threequartile_turns,
                    "25% quantile Turns":self.onequartile_turns,
                    "Mean nResults Reduct":self.mean_nResults_reduction,
                    "Harmonic mean nResult Reduct":self.harmonic_mean_nResults_reduction,
                    "Mean delta nResults":self.mean_delta_nResults,
                    "Mean delta Rank": self.mean_delta_Rank,
                    "Median Turns":self.median_Turns,
                    "Max Turns needed": self.max_turns_needed,
                    "Mean information gain": self.info_gain_mean
                    }
        return self.df,self.services,self.questions,self.means,self.conversations

    def add_deltas(self):
        nResults_reduction = []
        delta_nResults = []
        delta_Rank = []
        entropy =[]
        information_gain=[]
        i = 0
        while i < len(self.df):
            if self.df["t"].iloc[i] == 0:
                entropy.append(math.log(self.df["nResult"].iloc[i],2))
                information_gain.append(None)
                nResults_reduction.append(None)
                delta_nResults.append(None)
                delta_Rank.append(None)
            else:
                nResults_reduction.append(1 - self.df["nResult"].iloc[i] / self.df["nResult"].iloc[i - 1])
                delta_nResults.append(self.df["nResult"].iloc[i - 1] - self.df["nResult"].iloc[i])
                delta_Rank.append(self.df["rank"].iloc[i - 1] - self.df["rank"].iloc[i])
                entropy.append(math.log(self.df["nResult"].iloc[i],2))
                information_gain.append(entropy[i-1]-entropy[i])
            i += 1
        self.df["nResult_reduction"] = nResults_reduction
        self.df["delta_nResults"] = delta_nResults
        self.df["delta_Rank"] = delta_Rank
        self.df["entropy"] =entropy
        self.df["information gain"]=information_gain
        self.mean_nResults_reduction=self.df[self.df["question"]!='initialQuery']["nResult_reduction"].mean()
        self.info_gain_mean = self.df[self.df["question"]!='initialQuery']["information gain"].mean()
        self.harmonic_mean_nResults_reduction=statistics.harmonic_mean(self.df[self.df["question"]!='initialQuery']["nResult_reduction"])
        self.mean_delta_nResults = self.df[self.df["question"] != 'initialQuery']["delta_nResults"].mean()
        self.mean_delta_Rank = self.df[self.df["question"] != 'initialQuery']["delta_Rank"].mean()
        self.max_turns_needed = self.df["t"].max()
        self.services = self.df.copy()
        self.questions=self.df.copy()
        return self.df

    def aggregate_services(self):
        self.services = self.df.copy()
        self.services = self.services.groupby(["dialogId", "name"])["t"].agg('max').to_frame('turns').reset_index()
        self.mean_Turns=self.services['turns'].mean()
        self.ninety_centile_turns = self.services['turns'].quantile(0.9)
        self.threequartile_turns = self.services['turns'].quantile(0.75)
        self.onequartile_turns = self.services['turns'].quantile(0.25)
        self.median_Turns = self.services['turns'].median()
        self.conversations=self.services.copy()
        # self.services["turns"]=self.services_pre.groupby(["dialogId","name"])["t"].agg(turns='max')
        self.services = self.services.groupby(["name"]).agg(Count_Turns=('turns', 'count'), Min_Turns=('turns', 'min'),
                                      Mean_Turns=('turns', 'mean'), Max_Turns=('turns', 'max'))

        # self.services=self.services.groupby(["name"]).agg({'turns':['min','mean','max','count']})
        """
        self.services=self.services.groupby(["name","turns"])["turns"].agg('count').to_frame('Count_turns').reset_index()
        self.services=self.services.groupby(["name","turns"])["turns"].agg('min').to_frame('Min_turns').reset_index()
        self.services=self.services.groupby(["name","turns"])["turns"].agg('max').to_frame('Max_turns').reset_index()                                
        self.services=self.services.groupby(["name","turns"])["turns"].agg(np.mean).to_frame('Mean_turns').reset_index()
        """

        return self.services

    def aggregate_questions(self):
        self.questions=self.df.copy()
        self.questions = self.questions.groupby(["question"]).agg(Dialog_Count=('dialogId', 'count'), Services_Count=('name', 'nunique'),
                                          Min_Reduction=('nResult_reduction', 'min'),
                                          Mean_Reduction=('nResult_reduction', 'mean'),
                                          Max_Reduction=('nResult_reduction', 'max'), Mean_dRank=('delta_Rank', 'mean'))

        return self.questions