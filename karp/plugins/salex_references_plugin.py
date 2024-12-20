# TODO: make this into a general-purpose plugin

import re
from collections import defaultdict
from enum import Enum, global_enum
from functools import wraps

from injector import inject

from karp.foundation import json
from karp.lex.application import ResourceQueries
from karp.search.domain import QueryRequest
from karp.search.domain.query_dsl.karp_query_model import Equals, Freetext, Identifier, Or
from karp.search.infrastructure import EsSearchService

from .plugin import Plugin


@global_enum
class Id(Enum):
    LNR = 0
    XNR = 1
    KCNR = 2
    INR = 3
    SAOL_LNR = 4
    SAOL_XNR = 5


id_namespaces = {LNR: "so", XNR: "so", KCNR: "so", INR: "so", SAOL_LNR: "saol", SAOL_XNR: "saol"}

id_names = {LNR: "lnr", XNR: "xnr", KCNR: "kcnr", INR: "inr", SAOL_LNR: "lnr", SAOL_XNR: "xnr"}

id_fields = {
    "so.l_nr": LNR,
    "so.varianter.l_nr": LNR,
    "so.vnomen.l_nr": LNR,
    "so.förkortningar.l_nr": LNR,
    "so.huvudbetydelser.x_nr": XNR,
    "so.huvudbetydelser.underbetydelser.kc_nr": KCNR,
    "so.huvudbetydelser.idiom.i_nr": INR,
    "saol.id": SAOL_LNR,
    "saol.alt.id": SAOL_LNR,
    "saol.huvudbetydelser.id": SAOL_XNR,
}

ref_fields = {
    "so.huvudbetydelser.hänvisningar.hänvisning": None,
    "so.huvudbetydelser.morfex.hänvisning": None,
    "so.huvudbetydelser.underbetydelser.hänvisningar.hänvisning": None,
    "so.huvudbetydelser.underbetydelser.morfex.hänvisning": None,
    "so.huvudbetydelser.idiom.hänvisning": INR,
    "so.vnomen.hänvisning": None,
    "so.relaterade_verb.refid": LNR,
    "saol.moderverb": SAOL_LNR,
}


def find_ids(entry):
    for field, kind in id_fields.items():
        for path in json.expand_path(field, entry):
            ref = json.get_path(path, entry)
            yield kind, ref


def parse_ref(path, kind, ref):
    saol = path[0] == "saol"

    if kind is None:
        if ref.startswith("lnr"):
            ref = ref[3:]
            kind = SAOL_LNR if saol else LNR
        elif ref.startswith("xnr"):
            ref = ref[3:]
            kind = SAOL_XNR if saol else XNR
        elif ref.startswith("kcnr"):
            ref = ref[4:]
            kind = KCNR
        else:
            print("unknown reference", ref)
            return

    return kind, ref


def find_refs(entry):
    for field, kind in ref_fields.items():
        for path in json.expand_path(field, entry):
            ref = json.get_path(path, entry)
            result = parse_ref(path, kind, ref)
            if result:
                yield result

    for path in json.all_paths(entry):
        field = json.path_str(path)
        if field in ref_fields:
            continue

        if path and path[0] in ["so", "saol"]:
            value = json.get_path(path, entry)

            if not isinstance(value, str):
                continue
            results = re.findall(r"(?<=refid=)[a-zA-Z0-9]*", value)
            for ref in results:
                result = parse_ref(path, None, ref)
                if result:
                    yield result


def format_ref(kind, ref):
    return f"{id_namespaces[kind]}.{id_names[kind]}{ref}"


# A plugin that finds all references from a given item
class SalexForwardReferencesPlugin(Plugin):
    def output_config(self, **kwargs):
        return {"type": "string", "collection": "true"}

    def generate(self, entry):
        return [format_ref(kind, ref) for kind, ref in find_refs(entry)]


# A decorator to help with writing generate_batch. Collects batches
# into "sub-batches" and invokes generate_batch once on each sub-batch.
#
# Example: if batch items look like this:
#     {"resource": "salex", "field": "ortografi", "other": "xx"}
# Then you can define:
#     @group_batch_by("resource", "field")
#     def generate_batch(self, resource, field, batch):
#       ...
# The batch will be split into sub-batches, one sub-batch for each
# combination of "resource" and "field". Notice that "resource" and
# "field" become parameters to generate_batch. These fields are also
# removed from "batch", so the batch items will look like this:
#     {"other": "xx"}
def group_batch_by(*args):
    def batch_key(batch_item):
        return {arg: batch_item[arg] for arg in args}

    def batch_rest(batch_item):
        return {arg: batch_item[arg] for arg in batch_item if arg not in args}

    def inner(function):
        @wraps(function)
        def generate_batch(self, batch):
            batch = list(batch)

            # split the batch into sub-batches that all have the same key
            unfrozen_keys = {}
            sub_batches = defaultdict(dict)
            for i, item in enumerate(batch):
                frozen_key = str(batch_key(item))
                if frozen_key not in unfrozen_keys:
                    unfrozen_keys[frozen_key] = batch_key(item)

                sub_batches[frozen_key][i] = batch_rest(item)

            # run the plugin on all sub-batches
            results = {}
            for frozen_key, items in sub_batches.items():
                key = unfrozen_keys[frozen_key]
                sub_batch_results = list(function(self, **key, batch=list(items.values())))

                if len(sub_batch_results) != len(items):
                    raise AssertionError("size mismatch")

                for i, result in zip(items, sub_batch_results):
                    results[i] = result

            return [results[i] for i in range(len(batch))]

        return generate_batch

    return inner


# A plugin that finds all references to a given item.
# Designed to be used together with SalexForwardReferencesPlugin.
class SalexBackwardReferencesPlugin(Plugin):
    @inject
    def __init__(self, search_service: EsSearchService):
        self.search_service = search_service

    def output_config(self, resource, field, **kwargs):
        return {
            "type": "object",
            "collection": "true",
            "fields": {"id": {"type": "str"}, "ref": {"type": "str"}, "ortografi": {"type": "str"}},
        }

    @group_batch_by("resource", "field")
    def generate_batch(self, resource, field, batch):
        # collect all the ids and run one multi_query to find all of them
        item_ids = [{format_ref(kind, id) for kind, id in find_ids(item["entry"])} for item in batch]  # noqa: A001
        all_ids = list(set.union(*item_ids))

        requests = [
            QueryRequest(resources=[resource], q=Equals(field=Identifier(ast=field), arg=id), lexicon_stats=False)
            for id in all_ids  # noqa: A001
        ]
        query_results = self.search_service.multi_query(requests)

        def get_result(ref, entry):
            return {"id": entry["id"], "ref": ref, "ortografi": entry["entry"].get("ortografi", "")}

        id_references = {
            id: [get_result(id, entry) for entry in entries["hits"]]
            for id, entries in zip(all_ids, query_results)  # noqa: A001
        }

        # now collect the results
        result = []
        for ids in item_ids:
            references = []
            for id in ids:  # noqa: A001
                references += id_references.get(id, [])
            result.append(references)

        return result


# an old attempt, a bit slow
class SalexReferencesPluginOld(Plugin):
    @inject
    def __init__(self, resources: ResourceQueries, search_service: EsSearchService):
        self.resources = resources
        self.search_service = search_service

    def output_config(self, resource):
        return {"type": "string", "collection": "true"}

    def generate_batch(self, batch):
        def equals(field, id):  # noqa: A002
            return Equals(field=Identifier(ast=field), arg=id)

        def or_(queries):
            return Or(ast=queries)

        def freetext(text):
            return Freetext(arg=text)

        def make_request(resource, so, saol):
            conditions = []
            entry = {"so": so, "saol": saol}
            for kind, id in find_ids(entry):  # noqa: A001
                for field, kind2 in ref_fields.items():
                    if kind == kind2:
                        conditions.append(equals(field, id))
                    elif kind2 is None and kind in id_names:
                        conditions.append(equals(field, f"{id_names[kind]}{id}"))

                if kind in id_names:
                    conditions.append(freetext(f"{id_names[kind]}{id})"))

            return QueryRequest(resources=[resource], q=or_(conditions), lexicon_stats=False)

        requests = [make_request(**d) for d in batch]
        results = self.search_service.multi_query(requests)

        for result in results:
            hits = result["hits"]

            yield [hit["entry"].get("ortografi", "") for hit in hits]
