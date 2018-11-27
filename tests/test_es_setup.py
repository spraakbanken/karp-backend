import json
import urllib.request
import urllib.parse


def test_es_setup(es):
    url = 'http://localhost:' + str(es)
    f = urllib.request.urlopen(url)
    answer = json.loads(f.read().decode('utf-8'))
    assert answer['tagline'] == 'You Know, for Search'
