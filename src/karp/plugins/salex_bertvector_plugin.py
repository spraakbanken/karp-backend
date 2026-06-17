import re

from sentence_transformers import SentenceTransformer

from karp.globals import os_client

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
    def output_config(self, **resource):
        config = {
            "collection": True,
            "type": "string",
            #    "flatten_params": False,
        }
        return config

    def generate(self, ordklass, bertvector, resource):
        query = {
            "nested": {
                "path": "so.huvudbetydelser",
                "query": {
                    "knn": {
                        "so.huvudbetydelser._bertvector": {
                            "vector": bertvector,
                            "k": 10,
                            # TODO not supported in OpenSearch?
                            # "num_candidates": 500,
                            # possibly: "method_parameters": {"ef_search": 500},
                            "filter": {
                                "match": {
                                    "ordklass": ordklass,
                                }
                            },
                        }
                    }
                },
                "inner_hits": {
                    "_source": False,
                    "size": 1,
                    "fields": ["so.huvudbetydelser.x_nr"],
                },
            }
        }
        # https://docs.opensearch.org/latest/query-dsl/specialized/k-nn/index/

        res = os_client.search(size=11, body={"query": query}, index=resource)

        hits = []
        for item in res["hits"]["hits"]:
            orto = item["_source"]["ortografi"]
            homonr = ""
            if "homografNr" in item["_source"].keys():
                homonr = str(item["_source"]["homografNr"])

            for item2 in item["inner_hits"]["so.huvudbetydelser"]["hits"]["hits"]:
                # https://docs.opensearch.org/latest/search-plugins/searching-data/inner-hits/
                # or perhaps https://docs.opensearch.org/latest/vector-search/specialized-operations/nested-search-knn/
                # TODO ??
                num = item2["_nested"]["offset"]
                score = item2["_score"]
                hbet = item2["fields"]["so.huvudbetydelser.x_nr"][0]
                hits.append((homonr, orto, "xnr" + hbet, score))
        return hits[1:]


class BertVectorPlugin(Plugin):
    def output_config(self, config):
        config = {**config, "collection": True, "type": "dense_vector", "flatten_params": False}
        return config

    def generate(self, ortografi, böjning, betydelse, **kwargs):
        if entry_is_visible(betydelse):
            texten = ortografi + " " + böjning + " " + get_text(betydelse)
            texten = " ".join([texten] + [get_text(bet) for bet in betydelse.get("underbetydelser", [])])
            texten = clean_tags(clean_refs(texten))
            bertembedding = kbmodel.encode(texten)
            return bertembedding
