import spacy
from itertools import chain, groupby
from operator import itemgetter
from sklearn.cluster import DBSCAN
import gensim
import numpy as np
import spacy
import re
from sklearn.feature_extraction.text import CountVectorizer
from solrhandler import SolrHandler


def init_vector_ext(df, col_name="ssdsLemma"):
    """
    NOT USED IN LIVE CHATBOT
    :param df: the solr-df
    :param col_name: to be used column
    :return: word occurences, list & freq
    """
    # initiates the word-occurence & frequency vector and list of words
    vectorizer = CountVectorizer()
    # counts occurences
    a = vectorizer.fit_transform(df[f"{col_name}_processed"]).toarray()
    # boolean of weither or nor a bigger than 0
    b = a > 0
    # bool to int
    word_occ = b.astype(int)
    # collect all words
    words = vectorizer.get_feature_names()
    # sums word frequencie
    word_freq = word_occ.sum(axis=0).tolist()
    return word_occ, words, word_freq


def choose_question(length: object, word_freq: object) -> object:
    """

    :param length: length of current resultset
    :param word_freq: frequency matrix
    :return: index of KW for next question
    """
    # Chooses Index of Keywords with occurs closest to 50%
    #measure each occurence's quared distance to half length
    distance_matrix = [(length / 2 - y) ** 2 for y in word_freq]
    #get min distance
    tmp = min(distance_matrix)
    #get ID of min distance
    index = distance_matrix.index(tmp)
    return index

#not me, imported from other function

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


def process_df_col(df, column, do_preprocessing=True, nlp_model=spacy.load('de_core_news_lg')):
    values = df[column].tolist()
    if isinstance(values[0], list):
        values = [" ".join(val) for val in values]
    values = [clean_text(val, nlp_model) for val in values]
    if do_preprocessing:
        values = [preprocess_text(val, nlp_model) for val in values]
    df[f"{column}_processed"] = values  # TODO .loc
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


def refrain_results_ext(df, word_occ, word_freq, kw_index, choice):
    # returns updated word_occurence, frequency and dataframe to EXTERNAL
    df = df.drop(df.index[np.where(word_occ[:, kw_index] != choice)]).reset_index(drop=True)
    word_occ = word_occ[np.where(word_occ[:, kw_index] == choice)]
    word_freq = word_occ.sum(axis=0).tolist()
    return df, word_occ, word_freq


def iterate_through_all_keys(df_big, occ_big, freq_big, words_big, result_list_len=6):
    # iterates through all keywords
    # forming sub-DF with every keyword once as initial query
    # in each step runs "iterate_through_all_services"
    i = 0
    conversationtime = []
    while i < len(words_big):
        df, occ, freq = refrain_results_ext(df_big, occ_big, freq_big, i, 1)
        j = 0
        df_iter = iterate_through_all_services(df, occ, freq, result_list_len)
        i += 1
        conversationtime.append(df_iter["Conversations_needed"].mean())
    return conversationtime


def iterate_through_all_services(df, word_occ_big, word_freq_big, result_list_len=6):
    # iterates through all services in df
    # sets each one as target once and conversates with the backend of chatbot
    # gives back DF enriched by number of conversations (user feedback) it took to get to it
    df_give = df.copy()
    service = 0
    conversation_time = []
    while service < len(df_give):

        service_keys = word_occ_big[service, :]
        index = 0
        j = 0
        word_freq = word_freq_big
        word_occ = word_occ_big
        df = df_give.copy()
        while len(df) > result_list_len:
            index = choose_question(len(df), word_freq)
            choice = (service_keys[index])

            df, word_occ, word_freq = refrain_results_ext(df, word_occ, word_freq, index, choice)
            j += 1
        conversation_time.append(j)
        service += 1
    df_give["Conversations_needed"] = conversation_time
    return df_give

#Jakob

def preprocess_text(text, nlp_model):
    doc = nlp_model(text)
    text = " ".join([tok.lemma_ for tok in doc if not tok.is_stop and tok.is_alpha])
    return text.lower()

def get_unique_tokens(tokens):
    tokens_unique = []
    token_texts_unique= []
    for tok in tokens:
        if tok.text not in token_texts_unique:
            tokens_unique.append(tok)
            token_texts_unique.append(tok.text)
    return tokens_unique

def flatten_lst(lst):
    return list(chain(*lst))

def get_word2cluster_topic(clusters):
    word2cluster_topic = {}
    for cluster in clusters:
        for elem in cluster:
            word2cluster_topic.update({elem: cluster[0]})
    return word2cluster_topic

def drop_duplicates(lst):
    return list(set(lst))

def get_clusters(tokens, clustering):
    vecs = [tok.vector for tok in tokens]
    labels = clustering.fit_predict(vecs)
    elems = [(tok.text, label) for tok, label in zip(tokens, labels)]
    clusters = [[el[0] for el in elems if el[1] == i] for i in range(len(set(labels)))]
    return clusters

def get_keywords_clustered(lemma_lst, nlp_model, eps=0.2 ):
    clustering = DBSCAN(eps=eps, min_samples=1, metric="cosine")
    lemmas_tokens = [[tok for tok in doc] for doc in nlp_model.pipe(lemma_lst)]
    lemma_tokens_lst = get_unique_tokens(flatten_lst(lemmas_tokens))
    tokens_vectorizable = [tok for tok in lemma_tokens_lst if tok.has_vector]
    tokens_not_vectorizable = [tok for tok in lemma_tokens_lst if tok not in tokens_vectorizable]
    clusters = get_clusters(tokens_vectorizable, clustering)
    word2cluster_topic = get_word2cluster_topic(clusters)
    word2cluster_topic.update({tok.text: tok.text for tok in tokens_not_vectorizable})
    return [drop_duplicates([word2cluster_topic[tok.text] for tok in res]) for res in lemmas_tokens]


