import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import DBSCAN
import re


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

class Clusterer:

    def __init__(self, vectorizer = TfidfVectorizer(), clustering_algorithm = DBSCAN(eps=1.3, min_samples=1),
                 cluster_by = "ssdsLemma", nlp_model = spacy.load('de_core_news_lg')):
        self.vectorizer = vectorizer
        self.clustering_algorithm = clustering_algorithm
        self.cluster_by = cluster_by
        self.nlp_model = nlp_model

    def run(self, df, firstCall = True):
        """
            Returns Solar output in form of a dataframe with an annotation for the clustering for each resource.

                Parameters:
                        query (str): Solr query.
                        cluster_by (str): Resource description to perform clustering on.
                        do_preprocessing (bool): Weather or not to perform lemmatization and punctuation removal before
                        clustering.
                        query_max_elems (int): Maximum number of elements return by Solr sever.
                        cluster_eps (float): Epsilon parameter for DBSCAN clustering algorithm.
                        cluster_min_samples (int): Min_samples parameter for DBSCAN clustering algorithm.

                Returns:
                        df (pd.DataFrame): Solar output in form of a dataframe with an annotation for the clustering for
                        each resource.
        """
        # Preprocess column to be clustered
        if firstCall:
            df = process_df_col(df, self.cluster_by, True, self.nlp_model)



        # Clustering
        vectors = self.vectorizer.fit_transform(df[f"{self.cluster_by}_processed"].tolist())
        clusters = self.clustering_algorithm.fit(vectors).labels_
        df[self.getClusteredColumn()] = clusters # TODO .loc
        return df

    def getClusteredColumn(self):
        return f"{self.cluster_by}_cluster"


