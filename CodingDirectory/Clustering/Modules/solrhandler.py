import pandas as pd
import requests


def get_json_from_solr(query, max_elems=1000):
    query = query.replace(' ', '%20')
    url = f"http://localhost:8983/solr/d115Services/select?indent=true&q.op=OR&q={query}&rows={max_elems}"
    return requests.get(url).json()


def get_df_from_json(json_file):
    data = json_file["response"]["docs"]
    return pd.DataFrame.from_dict(data)

class SolrHandler():

    def __init__(self, max_elems = 1000):
        self.max_elems = max_elems

    def get_df_from_query(self, query):
        query_json = get_json_from_solr(query, max_elems=self.max_elems)
        df = get_df_from_json(query_json)
        if(len(df) == 0):
            raise Exception("no solr output")
        return df