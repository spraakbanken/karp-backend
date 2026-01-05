import re

import numpy as np
from sentence_transformers import SentenceTransformer

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


class BertVectorPlugin(Plugin):
    def output_config(self):  # noqa
        config = {"collection": True, "type": "float", "cache_plugin_expansion": False}
        return config

    def generate(self, ortografi, visas, böjning, betydelse):
        if visas and entry_is_visible(betydelse):
            texten = ortografi + " " + böjning + " " + get_text(betydelse)
            texten = " ".join([texten] + [get_text(bet) for bet in betydelse.get("underbetydelser", [])])
            texten = clean_tags(clean_refs(texten))
            print(texten)
            bertembedding = np.array(
                kbmodel.encode(texten)
            ).tolist()  # tolist() avoids "np.float_" issue in elasticsearch
            return bertembedding
        else:
            return np.zeros(768).tolist()
