# TODO: make this into a general-purpose plugin

import re
from enum import Enum, global_enum

from injector import inject

from karp.foundation import json
from karp.lex.application import ResourceQueries
from karp.search.domain import QueryRequest
from karp.search.domain.query_dsl.karp_query_model import Equals, Freetext, Identifier, Or
from karp.search.infrastructure import EsSearchService

from .plugin import Plugin, group_batch_by


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
    "so.huvudbetydelser.x_nr": XNR,
    "so.huvudbetydelser.underbetydelser.kc_nr": KCNR,
    "so.huvudbetydelser.idiom.i_nr": INR,
    "so.variantformer.l_nr": LNR,
    "so.vnomen.l_nr": LNR,
    "so.förkortningar.l_nr": LNR,
    "saol.id": SAOL_LNR,
    "saol.variantformer.id": SAOL_LNR,
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
    # "saol.enbartDigitalaHänvisningar.hänvisning": None, this is in +refid(...) form
    # "saol.huvudbetydelser.hänvisning": None, this is in +refid(...) form
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
    regexp = re.compile(r"(?<=refid=)[a-zA-Z0-9]*")

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
            results = regexp.findall(value)
            for ref in results:
                result = parse_ref(path, None, ref)
                if result:
                    yield result


def format_ref(kind, ref):
    return f"{id_namespaces[kind]}.{id_names[kind]}{ref}"


def flatten_list(x):
    if isinstance(x, list):
        for y in x:
            yield from flatten_list(y)
    else:
        yield x


# A plugin that finds all references from a given item
class SalexForwardReferencesPlugin(Plugin):
    def output_config(self, **kwargs):
        return {"type": "string", "collection": True}

    def generate(self, entry):
        return [format_ref(kind, ref) for kind, ref in find_refs(entry)]


# A plugin that finds all references to a given item.
# Designed to be used together with SalexForwardReferencesPlugin.
class SalexAllBackwardReferencesPlugin(Plugin):
    @inject
    def __init__(self, search_service: EsSearchService):
        self.search_service = search_service

    def output_config(self, resource, field, **kwargs):
        return {
            "type": "object",
            "collection": "true",
            "fields": {"from": {"type": "string"}, "to": {"type": "string"}},
        }

    @group_batch_by("resource", "field")
    def generate_batch(self, resource, field, batch):
        # collect all the ids and run one multi_query to find all of them
        item_ids = [
            {format_ref(kind, id) for kind, id in find_ids(item["entry"])}  # noqa: A001
            for item in batch
        ]
        all_ids = list(set.union(*item_ids))

        requests = [
            QueryRequest(
                resources=[resource], q=Equals(field=Identifier(ast=field), arg=id), lexicon_stats=False, size=None
            )
            for id in all_ids  # noqa: A001
        ]
        try:
            query_results = self.search_service.multi_query(requests)
        except KeyError:
            # can happen if forward references field hasn't been indexed yet
            query_results = []

        def get_result(ref, entry):
            return {"from": entry["entry"].get("ortografi", "?"), "to": ref}

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


# A plugin that finds all references to a given ID.
# Designed to be used together with SalexForwardReferencesPlugin.
class SalexBackwardReferencesPlugin(Plugin):
    @inject
    def __init__(self, search_service: EsSearchService):
        self.search_service = search_service

    def output_config(self, resource, field, **kwargs):
        # return {
        # "type": "object",
        # "collection": "true",
        # "fields": {"id": {"type": "string"}, "ref": {"type": "string"}, "ortografi": {"type": "string"}},
        # }
        return {"type": "string", "collection": True}

    @group_batch_by("resource", "field")
    def generate_batch(self, resource, field, batch):
        # collect all the ids and run one multi_query to find all of them
        item_ids = [
            {format_ref(Id[item["kind"]], id) for id in flatten_list(item["id"])}  # noqa: A001
            for item in batch
        ]
        all_ids = list(set.union(*item_ids))

        requests = [
            QueryRequest(
                resources=[resource], q=Equals(field=Identifier(ast=field), arg=id), lexicon_stats=False, size=None
            )
            for id in all_ids  # noqa: A001
        ]
        try:
            query_results = self.search_service.multi_query(requests)
        except KeyError:
            # can happen if forward references field hasn't been indexed yet
            query_results = []

        def get_result(ref, entry):
            # return {"id": entry["id"], "ref": ref, "ortografi": entry["entry"].get("ortografi", "")}
            return entry["entry"].get("ortografi", "?")

        id_references = {
            id: [get_result(id, entry) for entry in entries["hits"]]
            for id, entries in zip(all_ids, query_results)  # noqa: A001
        }

        # now collect the results
        result = []
        for ids, item in zip(item_ids, batch):
            references = []
            for id in ids:  # noqa: A001
                references += id_references.get(id, [])
            references += list(flatten_list(item.get("nested", [])))
            result.append(references)

        return result


# Pick out only those references starting with a given prefix
class SalexSubsetReferencesPlugin(Plugin):
    def output_config(self, **kwargs):
        # return {
        # "type": "object",
        # "collection": "true",
        # "fields": {"id": {"type": "string"}, "ref": {"type": "string"}, "ortografi": {"type": "string"}},
        # }
        return {"type": "string", "collection": True}

    def generate(self, references, prefix):
        return [entry["from"] for entry in references if entry["to"].startswith(prefix)]


# an old attempt, a bit slow
class SalexReferencesPluginOld(Plugin):
    @inject
    def __init__(self, resources: ResourceQueries, search_service: EsSearchService):
        self.resources = resources
        self.search_service = search_service

    def output_config(self, resource):
        return {"type": "string", "collection": True}

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

            return QueryRequest(resources=[resource], q=or_(conditions), lexicon_stats=False, size=None)

        requests = [make_request(**d) for d in batch]
        results = self.search_service.multi_query(requests)

        for result in results:
            hits = result["hits"]

            yield [hit["entry"].get("ortografi", "") for hit in hits]
