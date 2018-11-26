"""
Perform health checks on the server.

Used to perform readiness and liveness probes on the server.
"""

from flask import Blueprint, jsonify, request    # pyre-ignore

query_api = Blueprint('query_api', __name__)


def user_is_permitted(resource_id: str) -> bool:
    if resource_id == "protected":
        return False
    else:
        return True


class Resource(object):
    pass


class ResourceStore(object):
    def get_resource(self, id: str) -> Resource:
        return Resource()


resource_store = ResourceStore()


def log_arguments() -> None:
    print("--> Request arguments")
    print(" from: {}".format(request.args.get('from')))
    print(" size: {}".format(request.args.get('size')))


@query_api.route('/<resources>/query', methods=['GET'])
@query_api.route('/query/<resources>', methods=['GET'])
def query(resources):
    log_arguments()
    resources = resources.split(',')
    for resource_id in resources:
        resource = resource_store.get_resource(resource_id)
        if not user_is_permitted(resource_id):
            return jsonify({'status': 'forbidden'}), 403
        print("/query got resource: {resource}".format(resource=resource_id))
    return jsonify({'status': 'ok'}), 200
