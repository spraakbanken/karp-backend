# TODO: make this into a general-purpose plugin

import re
from collections import defaultdict
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
