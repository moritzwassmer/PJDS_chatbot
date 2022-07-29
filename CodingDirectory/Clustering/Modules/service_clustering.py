from sklearn.feature_extraction.text import TfidfVectorizer
import spacy

from service_clustering_helper import get_json_from_solr, get_df_from_json, process_lemmas, annotate_cluster_labels, \
    get_max_cluster_label, get_cluster_centroid


class ServiceClustering:

    def __init__(self, initial_query, clustering, max_results=3):
        self.initial_query = initial_query
        self.clustering = clustering
        self.max_results = max_results
        self.nlp_model = spacy.load("de_core_news_lg")
        self.tfidf_vectorizer = TfidfVectorizer()
        self.df_init = None

        self.df_current = None
        self.max_cluster_label_current = None
        self.topic_current = None

        self.initial_run()

    def initial_run(self):
        self.get_df_init_from_solr()
        self.annotate_df_init()
        self.df_current = self.df_init
        self.run_topic_extraction()

    def get_df_init_from_solr(self):
        json_res = get_json_from_solr(self.initial_query)
        self.df_init = get_df_from_json(json_res)

    def annotate_df_init(self):
        self.df_init["ssdsLemma_processed"] = self.df_init.apply(lambda row: process_lemmas(row.ssdsLemma, self.nlp_model), axis=1)
        self.df_init["tfidf_embedding"] = [row for row in self.tfidf_vectorizer.fit_transform(self.df_init.ssdsLemma_processed).toarray()]

    def run_topic_extraction(self):
        if not self.isFinished():
            self.df_current = annotate_cluster_labels(self.df_current, self.clustering)
            self.max_cluster_label_current = get_max_cluster_label(self.df_current)
            self.topic_current = get_cluster_centroid(self.df_current, self.max_cluster_label_current, self.nlp_model)

    def refineResultset(self, userResponse: bool) -> None:
        if userResponse:
            self.df_current = self.df_current[self.df_current.cluster_label == self.max_cluster_label_current]
        else:
            self.df_current = self.df_current[self.df_current.cluster_label != self.max_cluster_label_current]
        self.run_topic_extraction()

    def isFinished(self) -> bool:
        return len(self.df_current) <= self.max_results

    def generateQuestion(self) -> str:
        return f"Ist Ihre Frage zum Thema {self.topic_current} ?"

    def get_result_string(self) -> str:
        return self.df_current.d115Name.to_list()