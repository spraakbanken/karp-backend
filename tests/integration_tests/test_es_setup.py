# import json
# import urllib.request
# import urllib.parse
# import pytest  # pyre-ignore

# # from karp import search
# # from karp.elasticsearch import es_search

# entries = [
#     {
#         "code": 1,
#         "name": "test1",
#         "population": 3,
#         "area": 30000,
#         "density": 5,
#         "municipality": [1],
#     },
#     {
#         "code": 2,
#         "name": "test2",
#         "population": 6,
#         "area": 20000,
#         "density": 5,
#         "municipality": [1],
#     },
#     {
#         "code": 3,
#         "name": "test3",
#         "population": 4,
#         "area": 50000,
#         "density": 5,
#         "municipality": [2, 3],
#     },
# ]


# def init(client, es_status_code):
#     client_with_data = client(use_elasticsearch=True)
#     if es_status_code == "skip":
#         pytest.skip("elasticsearch disabled")

#     for entry in entries:
#         client_with_data.post(
#             "places/add",
#             data=json.dumps({"entry": entry}),
#             content_type="application/json",
#         )
#     return client_with_data


# def test_es_setup(es):
#     if es == "skip":
#         pytest.skip("elasticsearch disabled")

#     url = "http://localhost:9201"
#     f = urllib.request.urlopen(url)
#     answer = json.loads(f.read().decode("utf-8"))
#     assert answer["tagline"] == "You Know, for Search"


# def test_es_search(es, client_with_data_f):
#     if es == "skip":
#         pytest.skip("elasticsearch disabled")

#     client_with_data = init(client_with_data_f, es)

#     with client_with_data.application.app_context():
#         args = {"q": "equals|population|3"}
#         query = search.build_query(args, "places,municipalities")
#         ids = search.search_with_query(query)
#         assert len(ids["hits"]) == 1
#         print("ids[0] = {}".format(ids["hits"][0]))
#         assert "entry" in ids["hits"][0]
#         assert ids["hits"][0]["entry"]["population"] == 3


# def test_es_search2(es, client_with_data_f):
#     if es == "skip":
#         pytest.skip("elasticsearch disabled")

#     client_with_data = init(client_with_data_f, es)

#     with client_with_data.application.app_context():
#         args = {"q": "equals|population|3"}
#         query = search.build_query(args, "places,municipalities")
#         assert isinstance(query, es_search.EsQuery)
#         query.split_results = True
#         result = search.search_with_query(query)
#         assert "hits" in result
#         assert "places" in result["hits"]
#         assert "municipalities" in result["hits"]
#         assert len(result["hits"]["municipalities"]) == 0
#         assert len(result["hits"]["places"]) == 1
