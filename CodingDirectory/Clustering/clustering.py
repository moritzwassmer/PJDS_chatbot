from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import DBSCAN
import pandas

from clustering_helpers import get_json_from_solr, get_df_from_json, clean_text, preprocess_text


class Clustering:

    def __init__(self, nlp_model):
        self.nlp_model = nlp_model
        self.df = None

    def run(self, query, cluster_by="ssdsLemma", do_preprocessing=True, query_max_elems=20, cluster_eps=1.3,
            cluster_min_samples=1):
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
        self.get_df_from_query(query, max_elems=query_max_elems)
        self.process_df_col(col_name=cluster_by, do_preprocessing=do_preprocessing)
        self.get_clusters(col_name=cluster_by, eps=cluster_eps, min_samples=cluster_min_samples)
        return self.df

    def get_df_from_query(self, query, max_elems=20):
        query_json = get_json_from_solr(query, max_elems=max_elems)
        df = get_df_from_json(query_json)
        self.df = df

    def process_df_col(self, col_name="ssdsLemma", do_preprocessing=True):
        values = self.df[col_name].tolist()
        if isinstance(values[0], list):
            values = [" ".join(val) for val in values]
        values = [clean_text(val, self.nlp_model) for val in values]
        if do_preprocessing:
            values = [preprocess_text(val, self.nlp_model) for val in values]
        self.df[f"{col_name}_processed"] = values

    def get_clusters(self, col_name="ssdsLemma", eps=1.3, min_samples=1):
        vectorizer = TfidfVectorizer()
        clustering = DBSCAN(eps=eps, min_samples=min_samples)
        vectors = vectorizer.fit_transform(self.df[f"{col_name}_processed"].tolist())
        clusters = clustering.fit(vectors).labels_
        self.df[f"{col_name}_cluster"] = clusters
