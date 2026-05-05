from typing import Annotated

from fastapi import Query
from pydantic import Field

from karp import auth
from karp.api import dependencies as deps
from karp.api.dependencies.fastapi_injector import inject_from_req
from karp.api.schemas import BaseModel
from karp.auth.application.resource_permission_queries import ResourcePermissionQueries
from karp.lex.application import SearchQueries
from karp.plugins import Plugin
from karp.search.domain.query_request import QueryRequest


class SalexSpellcheckPlugin(Plugin):
    def create_router(self, resource_id: str, params: dict[str, str]):
        # imported here to avoid importing FastAPI in the CLI import tree; this shaves off 200 ms from the cold start of the CLI
        from fastapi import APIRouter, Depends, HTTPException, status

        router = APIRouter()

        class SpellcheckResult(BaseModel):
            not_found: Annotated[list[str], Field(description="Those of the given words that were not found in Salex.")]

        @router.get(
            "/spellcheck",
            summary="Spellcheck",
            description="Check which of the given words are not found in Salex. Looks in inflection tables and fields called 'ortografi'.",
        )
        def spellcheck(
            words: Annotated[
                str, Query(description="Words to be spellchecked. Should not contain whitespace or punctuation.")
            ],
            user: auth.User = Depends(deps.get_user),
            resource_permissions: ResourcePermissionQueries = Depends(deps.get_resource_permission_queries),
            search_queries: SearchQueries = Depends(inject_from_req(SearchQueries)),
        ) -> SpellcheckResult:
            # user must have READ access to salex
            if not resource_permissions.has_permission(auth.PermissionLevel.read, user, ["salex"]):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
            if words:
                words = words.split(",")
            else:
                words = ()
            q = """
            or(
            equals|saol._inflectiontable.rows.preform.form|{word}||
            equals|saol.variantformer._inflectiontable.rows.preform.form|{word}||
            equals|ortografi|{word}||
            equals|saol.variantformer.ortografi|{word}||
            equals|so.variantformer.ortografi|{word}||
            equals|so.huvudbetydelser.morfex.ortografi|{word}||
            equals|so.huvudbetydelser.underbetydelser.morfex.ortografi|{word}||
            equals|so.vnomen.ortografi|{word}||
            equals|so.förkortningar.ortografi|{word}
            )
            """
            qs = []
            for word in words:
                qs.append(QueryRequest(resources=["salex"], q=q.format(word=word)))
            query_results = search_queries.multi_query(qs, expand_plugins=False)

            not_found = []
            for word, res in zip(words, query_results, strict=True):
                if "salex" not in res["distribution"] or res["distribution"]["salex"] == 0:
                    not_found.append(word)
            return SpellcheckResult(not_found=not_found)

        return router

    def output_config(self, **kwargs):
        return {}
