import re
from collections import defaultdict
from typing import Any, Optional

from karp import auth
from karp.api import dependencies as deps
from karp.api.dependencies.fastapi_injector import inject_from_req
from karp.auth.application.resource_permission_queries import ResourcePermissionQueries
from karp.lex.application import SearchQueries
from karp.search.domain.query_request import QueryRequest

from .plugin import Plugin

umlauts = {"a": "ä", "o": "ö", "u": "ö", "å": "ä", "y": "ö"}

umlauts_ö = {"å": "ö", "y": "ö", "o": "ö"}

delimiters = "%+="
vowels = "aouåeiyäö"
alphabet = "abcdefghijklmnopqrstuvwxyzåäö"

consonants = "".join([c for c in alphabet if c not in "aouåeiyäö"])


class RuleNotPossible(Exception):
    """
    Rules should raise this exception when it was not possible to perform the rule, for example
    because a IndexError will/have occurred.
    """

    pass


def fv(s):
    # if only one vowel - do not remove it
    if len([c for c in s if c in vowels]) <= 1:
        return s

    if s[-2] in "aeiouy":
        s = s[0:-2] + s[-1:]
        if s[-3:-1] == "mm":
            s = s[:-2] + s[-1]
    return s


# double final consonant
def dk(s):
    # special case for k
    if s[-1] == "k":
        s = s[0:-1] + "ck"
    elif is_consonant(s[-1]):
        s = s + s[-1]
    return s


def ek(s):
    for i in reversed(range(0, len(s) - 1)):
        if s[i + 1] in "mnr" and s[i + 1] == s[i]:
            # found doubled m,n or r
            s = drop_index(i, s)
            break
        #   print(s)
        elif is_consonant(s[i + 1]):
            pass

    return s


def om(s, dct):
    for i in reversed(range(0, len(s))):
        if s[i] in dct:
            s = s[0:i] + dct[s[i]] + s[i + 1 :]
            break
    return s


def tj(s):
    for i in reversed(range(0, len(s))):
        if s[i] == "g":
            s = s[0:i] + "gj" + s[i + 1 :]
            break
    return s


# %ej - finds last occurrence of 'gju' or 'skju' or 'stjä' and removes j from it
def ej(s):
    drop_j = {"gju": "gu", "skju": "sku", "stjä": "stä"}
    for i in reversed(range(0, len(s) - 2)):
        for st in drop_j.keys():
            if s[i:].startswith(st):
                s = s[0:i] + drop_j[st] + s[i - 1 + len(st) + 1 :]
                break
    return s


def asc(s):
    if s[-1] in "sxzSXZ":
        return s
    else:
        return s + "s"


def ascc(s):
    # print(s)
    if s[-1] in "sxzSXZ":
        return s
    else:
        return s + ":s"


def is_vowel(c):
    return c in vowels


def is_consonant(c):
    return c in consonants


def always(c):
    return True


def remove_last(cond, s):
    try:
        if cond(s[-1]):
            return s[:-1]
        else:
            return s
    except IndexError:
        raise RuleNotPossible() from None


def drop_index(i, s):
    if i == 0:
        return s[1:]
    elif i == -1:
        return s[0:i]
    else:
        return s[0:i] + s[i + 1 :]


def replace_last_vowel(s, c):
    for i in reversed(range(0, len(s))):
        if s[i] in vowels:
            s = s[0:i] + c + s[i + 1 :]
            break
    return s


rules = {
    "%sp": lambda s: remove_last(always, s),
    "%sk": lambda s: remove_last(is_consonant, s),
    "%sv": lambda s: remove_last(is_vowel, s),
    "%ts": lambda s: remove_last(always, remove_last(always, s)),
    "%ss": lambda s: remove_last(lambda x: x == "s", s),
    "%fv": fv,  # remove last vowel if in [aeiou], make preceding double m single
    # (rymmas -> ryms, skrämmas -> skräms)
    "%dk": dk,  # double consonant
    "%ek": ek,  # make double consonant single
    "%om": lambda s: om(s, umlauts),  # umlaut on last occurrence of aouå
    "%avö": lambda s: om(s, umlauts_ö),
    "%tj": tj,  # last occurrence of g -> gj
    "%ej": ej,  # remove j from last occurrence of "skju", "gju" and "stjä"
    "%asc": asc,  # add "s" if stem does not end with s,x or z.
    "%ascc": ascc,  # # add ":s" if stem does not end with s,x or z.
}


# precondition:
# rules != "" and rules always contain at least one delimiter symbol
def get_first_step(rules):
    delims = [symbol for symbol in rules if symbol in delimiters]
    if not delims:
        return rules, ""

    if len(delims) == 1:
        return rules, ""
    elif rules[0] == "=":
        return "=", rules[1:]
    else:
        # the start position of the next rule
        pos = re.match("[" + delimiters + "]" "[^" + delimiters + "]+", rules).end()
        return rules[0:pos], rules[pos:]


def apply_rule(rule, s):
    if not [c for c in rule if c in delimiters]:
        return rule
    if rule == "=":
        return s

    elif rule.startswith("+"):
        return s + rule[1:].replace("/", "")
    elif rule.startswith("%av"):
        return replace_last_vowel(s, rule[3])
    else:
        return rules[rule](s)


def apply_rules(s, rules):
    if rules != "":
        step, remainder = get_first_step(rules)
        new_s = apply_rule(step, s)
        return apply_rules(new_s, remainder)
    else:
        return s


class InflectionPlugin(Plugin):
    def create_router(self, resource_id: str, params: dict[str, str]):
        # imported here to avoid importing FastAPI in the CLI import tree; this shaves off 200 ms from the cold start of the CLI
        from fastapi import APIRouter, Depends, HTTPException, status

        router = APIRouter()

        def find_match(
            lemma: str,
            include_wordforms: list[list[str]],
            exclude_wordforms: list[list[str]],
            rules: list[dict],
            kind: Optional[str],
        ):
            """
            Generate tables for lemma from each rule
            If wordforms are given, check that each wordform (and optionally tag) is in the table
            Return the matching tables + rule name
            """
            final_res = []
            for rule in rules:
                try:
                    table = self.generate(lemma, rule, kind)
                except RuleNotPossible:
                    # Exception thrown when executing the rule, counts as not matching
                    continue

                forms = []
                for table_elem in table:
                    for row in table_elem["rows"]:
                        for preform in row["preform"]:
                            forms.append([preform["form"], preform["tag"]])

                matching = True
                for wordforms, test in (
                    # matching = False if form NOT in table
                    (include_wordforms, lambda x, y: x not in y),
                    # matching = False if form IS in table
                    (exclude_wordforms, lambda x, y: x in y),
                ):
                    for wordform in wordforms:
                        # wordform can either be just a form or a list of [form, tag]
                        if len(wordform) > 1:
                            tmp_forms = forms
                        else:
                            tmp_forms = [form[0] for form in forms]
                            wordform = wordform[0]
                        if test(wordform, tmp_forms):
                            matching = False
                            break

                if matching:
                    final_res.append({"name": rule["name"], "inflectiontable": table})
            return final_res

        def parse_wordforms(wordforms: str | None):
            """
            Parse query param for wordforms "wf1|tag1,wf2,wf3|tag"
            """
            return [wf.split("|") for wf in wordforms.split(",")] if wordforms else []

        @router.get(
            "/generate_inflection_table",
            summary="Generate inflection table",
            description="Given a lemma and an inflection class, generate an inflection table.",
        )
        def generate_inflection_table(
            lemma: str,
            inflection_class: Optional[str] = None,
            wordforms: Optional[str] = None,
            exclude_wordforms: Optional[str] = None,
            kind: Optional[str] = None,
            user: auth.User = Depends(deps.get_user_optional),
            resource_permissions: ResourcePermissionQueries = Depends(deps.get_resource_permission_queries),
            search_queries: SearchQueries = Depends(inject_from_req(SearchQueries)),
        ) -> list[Any]:
            # user must have READ access to the resource publishing this route
            if not resource_permissions.has_permission(auth.PermissionLevel.read, user, [resource_id]):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

            if inflection_class:
                # TODO maybe remove the parameter and just use name
                q = f"equals|{params['target']}|{inflection_class}"
            else:
                q = None

            # fetch the rules
            # TODO q should be optional
            if q:
                res = search_queries.query(QueryRequest(resources=[resource_id], q=q))
            else:
                res = search_queries.query(QueryRequest(resources=[resource_id], size=9999))
            rules = [hit["entry"] for hit in res["hits"]]

            # use the given lemma and rules to produce a table
            return find_match(lemma, parse_wordforms(wordforms), parse_wordforms(exclude_wordforms), rules, kind)

        return router

    def output_config(self):  # noqa
        config = {
            "collection": True,
            "type": "object",
            "fields": {
                "heading": {"type": "string"},
                "rows": {
                    "collection": True,
                    "type": "object",
                    "fields": {
                        "linenumber": {"type": "number"},
                        "preform": {
                            "collection": True,
                            "type": "object",
                            "fields": {
                                "prescript": {"type": "string"},
                                "form": {"type": "string"},
                                "tag": {"type": "string"},
                            },
                        },
                        "postscript": {"type": "string"},
                        "extra": {"type": "string"},
                    },
                },
            },
            "cache_plugin_expansion": False,
        }

        return config

    def generate(self, lemma, table, kind):
        if "definition" in table.keys():
            definitioner = table["definition"]
        else:
            definitioner = []
        tabellrader = defaultdict(list)
        particles = []
        moderverb = lemma
        if kind in ["partikelverb", "reflexivt_verb"]:
            splts = lemma.split(" ")
            moderverb = splts[0]
            particles = splts[1:]

        for defi in definitioner:
            if defi["prescript"] is None:
                raise
            rownr = defi["row"]
            rules = defi["rules"]

            inflected_form = apply_rules(moderverb, rules)

            heading = defi["heading"]
            tagg = defi["tagg"]
            if kind == "reflexivt_verb" or "sig" in particles:
                if any(tagg.startswith(s) for s in ["AP0", "AF0"]) or tagg.endswith("P") or tagg == "V0M0A":
                    # No particip, passiv or imperativ for reflexive verbs
                    continue

            if particles:
                if "particip" in heading:
                    inflected_form = "".join(particles) + inflected_form
                # elif 'passiv' in defi["postscript"] :
                #  inflected_form  = ' '.join([inflected_form] + particles) + " (" + ''.join(particles) + inflected_form + ")"

                else:
                    inflected_form = " ".join([inflected_form] + particles)

            if tabellrader[heading] and tabellrader[heading][-1]["linenumber"] == rownr:
                last_row = tabellrader[heading].pop()
                last_row["preform"].append((defi["prescript"], inflected_form, defi["tagg"]))
                tabellrader[heading].append(last_row)

            else:
                tabellrader[heading].append(
                    {
                        "preform": [(defi["prescript"], inflected_form, defi["tagg"])],
                        "postscript": defi["postscript"],
                        "extra": defi["extra"],
                        "linenumber": rownr,
                    }
                )
        the_result = []

        for heading in tabellrader.keys():
            heading_rows = tabellrader[heading]
            rows = []
            for hr in heading_rows:
                linenumber = hr["linenumber"]

                preforms = []
                preforms_hr = hr["preform"]

                if hr["preform"] is None:
                    raise Exception(tabellrader)

                for pf in preforms_hr:
                    if type(pf) is not tuple:
                        raise Exception(preforms, pf, type(pf))

                    preforms.append({"prescript": pf[0], "form": pf[1], "tag": pf[2]})

                row = {
                    "linenumber": hr["linenumber"],
                    "preform": preforms,
                    "postscript": hr["postscript"],
                    "extra": hr["extra"],
                }

                rows.append(row)

            obj = {"heading": heading, "rows": rows}

            the_result.append(obj)

        return the_result
