import pandas as pd
import requests
import re


def get_json_from_solr(query, max_elems):
    query = query.replace(' ', '%20')
    url = f"http://localhost:8983/solr/d115Services/select?indent=true&q.op=OR&q=*{query}*&rows={max_elems}"
    return requests.get(url).json()


def get_df_from_json(json_file):
    data = json_file["response"]["docs"]
    return pd.DataFrame.from_dict(data)


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