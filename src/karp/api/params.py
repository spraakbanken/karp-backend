from fastapi import Query

query_param = Query(
    None,
    title="query",
    description="""The query. If missing, all entries of the chosen
    resource(s) are returned/used. See [Query DSL](#section/Query-DSL).""",
)
