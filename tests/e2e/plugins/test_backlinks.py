"""
This plugin tests backlink_plugin.py
The plugin does not support searching on backlinks so we can only test that the
data looks correct
"""

from collections import defaultdict

import pytest

from karp.main import new_session
from karp.resource_commands import ResourceCommands
from tests import common_data, utils
from tests.e2e.conftest import AccessToken, create_and_publish_resource


@pytest.fixture(scope="module", name="fa_backlink_data_client")
def fixture_fa_data_client(  # noqa: ANN201
    fa_client,
    admin_token: AccessToken,
):
    create_and_publish_resource(
        fa_client,
        path_to_config="assets/testing/config/places.yaml",
    )
    create_and_publish_resource(
        fa_client,
        path_to_config="assets/testing/config/municipalities_with_backlink.yaml",
    )
    utils.add_entries(
        fa_client,
        {"municipalities": common_data.MUNICIPALITIES, "places": common_data.PLACES},
        access_token=admin_token,
    )

    yield fa_client

    with new_session(fa_client.app.state.app_context.injector) as injector:
        resource_commands = injector.get(ResourceCommands)

        resource_commands.delete_resource("places")
        resource_commands.delete_resource("municipalities")


def test_backlink(fa_backlink_data_client):
    places = fa_backlink_data_client.get("/query/places?size=100").json()

    # collect the expected results
    expects = defaultdict(list)
    for place in places["hits"]:
        entry = place["entry"]
        for munic_code in entry["municipality"]:
            expects[munic_code].append(entry["code"])

    # check that the data from the baclink plugin is the same as expected
    munics = fa_backlink_data_client.get("/query/municipalities?size=100").json()
    for munic in munics["hits"]:
        entry = munic["entry"]
        assert expects[entry["code"]] == entry["_places"]
