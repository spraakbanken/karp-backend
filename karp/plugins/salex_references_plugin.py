# TODO: make this into a general-purpose plugin

import re
from collections import defaultdict
from copy import deepcopy
from enum import Enum, global_enum

from injector import inject

from karp.foundation import json
from karp.lex.application import SearchQueries
from karp.search.domain import QueryRequest
from karp.search.domain.query_dsl.karp_query_model import Identifier, TextArgExpression

from .plugin import INDEXED, Plugin, flatten_list, group_batch_by


def entry_is_visible(entry):
    return not isinstance(entry, dict) or entry.get("visas", True)


def is_visible(path, entry, test=entry_is_visible):
    path = json.make_path(path)
    for i in range(len(path) + 1):
        if not test(json.get_path(path[:i], entry)):
            return False

    return True


def trim_invisible(data, test=entry_is_visible):
    paths = list(json.all_paths(data))  # compute up front since we will be modifying data
    for path in paths:
        if not json.has_path(path, data):
            continue  # already deleted

        value = json.get_path(path, data)
        if isinstance(value, dict) and not test(value):
            json.del_path(path, data)


def visible_part(data, test=entry_is_visible):
    data = deepcopy(data)
    trim_invisible(data, test)
    return data


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

standard_info = {
    "ortografi": "ortografi",
    "ordklass": "ordklass",
    "ingångstyp": "ingångstyp",
}

so_info = standard_info | {"homografNr": "so.homografNr"}
so_hb_info = so_info | {"huvudbetydelseNr": "so.huvudbetydelser.h_nr"}
saol_info = standard_info | {"homografNr": "saol.homografNr"}
saol_hb_info = saol_info | {"huvudbetydelseNr": "saol.huvudbetydelser.h_nr"}

ids_info = {
    "so.l_nr": so_info,
    "so.huvudbetydelser.x_nr": so_hb_info,
    "so.huvudbetydelser.underbetydelser.kc_nr": so_hb_info,
    "so.huvudbetydelser.idiom.i_nr": so_hb_info,  # more?
    "so.variantformer.l_nr": so_info
    | {
        "ortografi": "so.variantformer.ortografi",
    },
    "so.vnomen.l_nr": so_info
    | {
        "ortografi": "so.vnomen.ortografi",
        "homografNr": "so.vnomen.homografNr",
    },
    "so.förkortningar.l_nr": so_info
    | {
        "ortografi": "so.vnomen.ortografi",
        "homografNr": "so.vnomen.homografNr",
    },
    "saol.id": saol_info,
    "saol.variantformer.id": saol_info
    | {
        "ortografi": "saol.variantformer.ortografi",
    },
    "saol.huvudbetydelser.id": saol_hb_info,
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


def parse_ref(entry, path, kind, ref):
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
            print("unknown reference", entry["ortografi"], path, ref)
            return

    return kind, ref


def find_refs(entry):
    regexp = re.compile(r"(?<=refid=)[a-zA-Z0-9]*")

    for field, kind in ref_fields.items():
        for path in json.expand_path(field, entry):
            ref = json.get_path(path, entry)
            result = parse_ref(entry, path, kind, ref)
            if result:
                yield path, result

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
                result = parse_ref(entry, path, None, ref)
                if result:
                    yield path, result


def format_ref(kind, ref):
    return f"{id_namespaces[kind]}.{id_names[kind]}{ref}"


# A plugin that finds all references from a given item
class SalexForwardReferencesPlugin(Plugin):
    def output_config(self, **kwargs):
        return {
            "type": "object",
            "collection": True,
            "cache_plugin_expansion": False,
            "fields": {"visas": {"type": "boolean"}, "ref": {"type": "string"}},
        }

    def generate(self, entry):
        # maps kind, ref to visas
        refs = defaultdict(lambda: False)
        for path, (kind, ref) in find_refs(entry):
            # a ref with visas: True overrides one with visas: False
            # but not the other way round
            visible = is_visible(path, entry)
            refs[kind, ref] = refs[kind, ref] or visible

        return [{"visas": visible, "ref": format_ref(kind, ref)} for (kind, ref), visible in refs.items()]


# A plugin that finds all references to a given ID.
# Designed to be used together with SalexForwardReferencesPlugin.
class SalexBackwardReferencesPlugin(Plugin):
    @inject
    def __init__(self, search_queries: SearchQueries):
        self.search_queries = search_queries

    def output_config(self, resource, field, **kwargs):
        return {
            "type": "object",
            "collection": True,
            "allow_missing_params": True,
            "flatten_params": False,
            "searchable": False,
            "fields": {
                "id": {"type": "string"},
                "ortografi": {"type": "string"},
                "homografNr": {"type": "integer"},
                "visas": {"type": "boolean"},
                "subobject": {"type": "boolean"},
            },
        }

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
                resources=[resource],
                q=TextArgExpression(op="equals", field=Identifier(ast=field + ".ref"), arg=id),
                lexicon_stats=False,
                size=None,
            )
            for id in all_ids  # noqa: A001
        ]
        query_results = self.search_queries.multi_query(requests, expand_plugins=INDEXED)

        def get_result(id, entry):  # noqa: A002
            result = {"id": entry["id"], "ortografi": entry["entry"].get("ortografi", "?")}

            if id.startswith("so."):
                homografNr = entry["entry"].get("so", {}).get("homografNr")
            elif id.startswith("saol."):
                homografNr = entry["entry"].get("saol", {}).get("homografNr")
            else:
                raise AssertionError(f"ref doesn't start with so or saol: {id}")
            if homografNr is not None:
                result["homografNr"] = homografNr

            # To calculate "visas", we must get the list of references and find the appropriate one
            refs = json.get_path(field, entry["entry"])
            matches = [x for x in refs if x["ref"] == id]
            if len(matches) != 1:
                raise AssertionError(f"inconsistent search result, got {len(matches)} matches")
            result["visas"] = matches[0]["visas"]

            result["subobject"] = False  # put this here so it comes last in the JSON
            return result

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
            for ref in flatten_list(item.get("nested", [])):
                if ref is not None:
                    references.append(ref | {"subobject": True})
            result.append(references)

        return result


# A plugin that collects information about all ids
class SalexIdInfoPlugin(Plugin):
    def output_config(self, **kwargs):
        return {
            "type": "object",
            "collection": True,
            "additional_properties": True,
            "cache_plugin_expansion": False,
            "fields": {"id": {"type": "string"}},
        }

    def generate(self, entry):
        result = []
        entry = visible_part(entry)  # get rid of invisible huvudbetydelser before adding h_nr

        # Add {so,saol}.huvudbetydelser.h_nr fields
        for namespace in ["so", "saol"]:
            for path in json.expand_path(namespace + ".huvudbetydelser", entry, expand_arrays=False):
                values = json.get_path(path, entry)
                if len(values) > 1:
                    for i, value in enumerate(values, start=1):
                        value["h_nr"] = i

        for field, info in ids_info.items():
            for path in json.expand_path(field, entry):
                id = json.get_path(path, entry)
                prefix = id_namespaces[id_fields[field]] + "." + id_names[id_fields[field]]
                id_info = {"id": prefix + id}
                for key, value_field in info.items():
                    value_path = json.localise_path(value_field, path)
                    if json.has_path(value_path, entry):
                        value = json.get_path(value_path, entry)
                    else:
                        value = None
                    id_info[key] = value

                result.append(id_info)

        return result


# A plugin that collects information about reference targets.
# Designed to be used together with SalexIdInfoPlugin
class SalexReferenceInfoPlugin(Plugin):
    @inject
    def __init__(self, search_queries: SearchQueries):
        self.search_queries = search_queries

    def output_config(self, **kwargs):
        return {
            "searchable": False,
            "type": "object",
            "collection": True,
            "additional_properties": True,
            "fields": {"id": {"type": "string"}},
        }

    @group_batch_by("resource", "prefix", "field")
    def generate_batch(self, resource, prefix, field, batch):
        prefix = prefix or ""
        # collect all the ids and run one multi_query to find all of them
        # It would make more sense to run a single query, but that doesn't work
        # as ES can't return more than 10000 results
        all_ids = {ref["ref"] for item in batch for ref in item["references"] if ref["visas"]}

        requests = [
            QueryRequest(
                resources=[resource],
                q=TextArgExpression(op="equals", field=Identifier(ast=field + ".id"), arg=id),
                lexicon_stats=False,
                size=None,
            )
            for id in all_ids  # noqa: A001
        ]
        query_results = self.search_queries.multi_query(requests, expand_plugins=INDEXED)

        # Now collect all info for all returned id numbers
        all_id_info = {}
        for query_result in query_results:
            for entry in query_result["hits"]:
                for id_info in json.get_path(field, entry["entry"]):
                    all_id_info[id_info["id"]] = id_info

        # now collect the results
        def get_result(item):
            result = []
            for id in {ref["ref"] for ref in item["references"] if ref["visas"]}:
                if id.startswith(prefix) and id in all_id_info:
                    id_info = deepcopy(all_id_info[id])
                    id_info["id"] = id[len(prefix) :]  # strip prefix
                    result.append(id_info)
            return result

        return [get_result(item) for item in batch]
