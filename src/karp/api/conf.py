import json
from flask import Blueprint  # pyre-ignore
from flask import jsonify as flask_jsonify  # pyre-ignore

import karp.resourcemgr as resourcemgr

conf_api = Blueprint("conf_api", __name__)


@conf_api.route("/resources", methods=["GET"])
def get_resources():
    resources = resourcemgr.get_available_resources()
    result = []
    for resource in resources:
        resource_obj = {"resource_id": resource.resource_id}

        config_file = json.loads(resource.config_file)
        protected_conf = config_file.get("protected")
        if not protected_conf:
            protected = None
        elif protected_conf.get("admin"):
            protected = "ADMIN"
        elif protected_conf.get("write"):
            protected = "WRITE"
        else:
            protected = "READ"

        if protected:
            resource_obj["protected"] = protected
        result.append(resource_obj)

    return flask_jsonify(result)
