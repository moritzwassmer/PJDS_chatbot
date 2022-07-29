import requests
import pandas as pd
import numpy as np


def get_json_from_solr(query, max_elems=1000):
    query = query.replace(' ', '%20')
    url = f"http://localhost:8983/solr/d115Services/select?indent=true&q.op=OR&q={query}&rows={max_elems}"
    return requests.get(url).json()


def get_df_from_json(json_file):
    data = json_file["response"]["docs"]
    return pd.DataFrame.from_dict(data)


def process_lemmas(lst_lemmas, nlp_model):
    doc = nlp_model(" ".join(lst_lemmas))
    lemma_str = " ".join([tok.lemma_ for tok in doc if tok.is_alpha and not tok.is_stop])
    return lemma_str


def annotate_cluster_labels(df, clustering):
    cluster_labels = clustering.fit(df.tfidf_embedding.tolist()).labels_
    if hasattr(clustering, "eps"):
        cluster_labels = iterate_eps(cluster_labels, df, clustering)
    df["cluster_label"] = cluster_labels
    return df


def iterate_eps(cluster_labels, df, clustering):
    default_eps = clustering.eps
    while len(set(cluster_labels)) < 2:
        clustering.eps -= .1
        cluster_labels = clustering.fit(df.tfidf_embedding.tolist()).labels_
    clustering.eps = default_eps
    return cluster_labels


def get_max_cluster_label(df):
    cluster_labels = df.cluster_label.tolist()
    return max(set(cluster_labels), key=lambda x: cluster_labels.count(x))


def get_cluster_centroid(df, cluster_label, nlp_model):
    df_cluster = df[df.cluster_label == cluster_label]
    lemmas = df_cluster.ssdsLemma_processed.tolist()
    lemma_toks_vectorizable = [tok for doc in nlp_model.pipe(lemmas) for tok in doc if tok.has_vector]
    dist_matrix = np.asarray([[tok_1.similarity(tok_2) for tok_2 in lemma_toks_vectorizable] for tok_1 in lemma_toks_vectorizable])
    idx_centroid = dist_matrix.sum(axis=1).argmax()
    return lemma_toks_vectorizable[idx_centroid].text
