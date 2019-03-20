import karp.resourcemgr.entrywrite as entrywrite
import karp.resourcemgr.entryread as entryread
import karp.resourcemgr as resourcemgr
import karp.network as network

places = [
    {
        'code': 3,
        'name': 'a',
        'municipality': [1]
    },
    {
        'code': 4,
        'name': 'b',
        'municipality': [2, 3]
    },
    {
        'code': 5,
        'name': 'c',
        'municipality': [2, 3],
        'larger_place': 4
    }
]


def test_diff(app_with_data_f):
    app = app_with_data_f()

    with app.app_context():
        entrywrite.add_entries('places', [places[0]], 'test', resource_version=1)
        new_entry = places[0]
        new_entry['name'] = 'b'
        entrywrite.update_entry('places', '3', 1, new_entry, 'test', message='message', resource_version=1)

        diff = entryread.diff(resourcemgr.get_resource('places', 1), '3', 1, 2)
        assert len(diff) == 1
        assert diff[0]['type'] == 'CHANGE'
        assert diff[0]['before'] == 'a'
        assert diff[0]['after'] == 'b'
        assert diff[0]['field'] == 'name'
