from flask import Blueprint, jsonify, request  # pyre-ignore

import karp.auth.auth as auth
import karp.resourcemgr.entryread as entryread
import karp.resourcemgr as resourcemgr
import karp.errors as errors

history_api = Blueprint("history_api", __name__)


@history_api.route("/<resource_id>/<entry_id>/diff", methods=["GET", "POST"])
@auth.auth.authorization("ADMIN")
def get_diff(resource_id, entry_id):
    from_version = request.args.get("from_version")
    to_version = request.args.get("to_version")
    from_date_str = request.args.get("from_date")
    to_date_str = request.args.get("to_date")
    from_date = None
    to_date = None
    try:
        if from_date_str:
            from_date = float(from_date_str)
        if to_date_str:
            to_date = float(to_date_str)
    except ValueError:
        raise errors.KarpError("Wrong date format", code=50)

    diff_parameters = {
        "from_date": from_date,
        "to_date": to_date,
        "from_version": from_version,
        "to_version": to_version,
        "entry": request.get_json(),
    }

    diff, from_version, to_version = entryread.diff(
        resourcemgr.get_resource(resource_id), entry_id, **diff_parameters
    )
    result = {"diff": diff, "from_version": from_version}
    if to_version:
        result["to_version"] = to_version
    return jsonify(result)


@history_api.route("/<resource_id>/history", methods=["GET"])
@auth.auth.authorization("ADMIN")
def get_history(resource_id):
    history_parameters = {}
    from_date_str = request.args.get("from_date")
    to_date_str = request.args.get("to_date")
    try:
        if from_date_str:
            from_date = float(from_date_str)
            history_parameters["from_date"] = from_date
        if to_date_str:
            to_date = float(to_date_str)
            history_parameters["to_date"] = to_date
    except ValueError:
        raise errors.KarpError("Wrong date format", code=50)

    user_id = request.args.get("user_id")
    if user_id:
        history_parameters["user_id"] = user_id
    entry_id = request.args.get("entry_id")
    if entry_id:
        history_parameters["entry_id"] = entry_id
        from_version = request.args.get("from_version")
        to_version = request.args.get("to_version")
        if from_version:
            history_parameters["from_version"] = from_version
        if to_version:
            history_parameters["to_version"] = to_version

    history_parameters["current_page"] = int(request.args.get("current_page", 0))
    history_parameters["page_size"] = int(request.args.get("page_size", 100))

    history, total = entryread.get_history(resource_id, **history_parameters)
    return jsonify({"history": history, "total": total})


@history_api.route("/<resource_id>/<entry_id>/<version>/history", methods=["GET"])
@auth.auth.authorization("ADMIN")
def get_history_for_entry(resource_id, entry_id, version):
    historical_entry = entryread.get_entry_history(resource_id, entry_id, version)
    return jsonify(historical_entry)
