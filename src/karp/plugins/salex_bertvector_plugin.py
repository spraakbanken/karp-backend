import re

import numpy as np
from sentence_transformers import SentenceTransformer
from injector import inject
from elasticsearch import Elasticsearch
from .plugin import Plugin

kbmodel = SentenceTransformer("KBLab/sentence-bert-swedish-cased")


def entry_is_visible(entry):
    return entry.get("visas", True)


def clean_refs(text):
    pattern = re.compile(r"\+([\w\- ]*)(\(refid=)[\w\d]*\)")
    return re.sub(pattern, r"\1", text)


def clean_tags(text):
    pattern = re.compile(r"\[i ([\w -0-9]*)\]")
    return re.sub(pattern, r"\1", text)


def get_text_parts(textfield, field, entry):
    return [entry.get(textfield, "") for item in entry.get(field, []) if entry_is_visible(item)]


def get_text(entry):
    text = ""
    if entry_is_visible(entry):
        ämnesområden = entry.get("ämnesområden", [])
        text = " ".join([äo.get("ämne", "") for äo in ämnesområden])
        text = text + " " + entry.get("definition", "")
        text = text + " " + entry.get("definitionstillägg", "")
        text = " ".join([text] + get_text_parts("text", "syntex", entry))
        text = " ".join([text] + get_text_parts("ortografi", "morfex", entry))
        text = " ".join([text] + get_text_parts("ortografi", "_inkommande_hänvisningar", entry))
    return text


class NearestNeighboursPlugin(Plugin):
  
       @inject
       def __init__(self, es : Elasticsearch):
            self.es = es
 
       def output_config(self,**resource) : 
            config = {"collection" : True,
                      "type" : "string"
                  #    "flatten_params": False,                
            }
            return config
            
       def generate(self,ordklass,bertvector,resource) : 
                
                query = {
                         "nested" : {
                            "path" : "so.huvudbetydelser",
                            "query" : {
                                 "knn": {
                                    "query_vector": bertvector,
                                    "field": "so.huvudbetydelser._bertvector",
                                    "k" : 10,
               
                                    "num_candidates" : 500,
                    
                                   "filter": {
                                        "match": {
                                            "ordklass": ordklass,
                                        }
                                    }
                                }
                            },
                                "inner_hits": {
                                    "_source" : False,
                                    "size" : 1,
                                    "fields"  : ["so.huvudbetydelser.x_nr"],  
                                 }
                           }
                        }
                # https://www.elastic.co/docs/reference/query-languages/query-dsl/query-dsl-knn-query#knn-query-filtering

                res = self.es.search(size=11, query=query,index=resource) 
               
                hits = []
                for item in (res['hits']['hits']) : 
                  orto = item['_source']['ortografi']
                  homonr = ""
                  if 'homografNr' in item['_source'].keys() : 
                    homonr = str(item['_source']['homografNr'])   
                     
                  for item2 in item['inner_hits']['so.huvudbetydelser']['hits']['hits'] : 
                    #https://www.elastic.co/docs/reference/elasticsearch/rest-apis/retrieve-inner-hits
                      num = item2['_nested']['offset']
                      score = item2['_score']
                      hbet = item2['fields']['so.huvudbetydelser'][0] 
                      hits.append((homonr,orto,"xnr" + hbet['x_nr'][0],score))
                return hits[1:]

class BertVectorPlugin(Plugin):
    def output_config(self,config):
        config = {**config, "collection": True, "type": "dense_vector", "flatten_params": False}
        return config

    def generate(self, ortografi, böjning, betydelse, **kwargs):
        if entry_is_visible(betydelse):
            texten = ortografi + " " + böjning + " " + get_text(betydelse)
            texten = " ".join([texten] + [get_text(bet) for bet in betydelse.get("underbetydelser", [])])
            texten = clean_tags(clean_refs(texten))
            bertembedding = kbmodel.encode(texten)
            return bertembedding
     