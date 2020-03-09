"""
Builds OpenAPI spec and serves it
"""
import pkg_resources

from flask import Blueprint, url_for, Response  # pyre-ignore

documentation = Blueprint("documentation", __name__)


@documentation.route("/", methods=["GET"])
def get_documentation():
    html = """
    <!DOCTYPE html>
    <html>
      <head>
        <title>ReDoc</title>
        <!-- needed for adaptive design -->
        <meta charset="utf-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://fonts.googleapis.com/css?family=Montserrat:300,400,700|Roboto:300,400,700" rel="stylesheet">

        <!--
        ReDoc doesn't change outer page styles
        -->
        <style>
          body {
            margin: 0;
            padding: 0;
          }
        </style>
      </head>
      <body>
        <redoc spec-url='%s'></redoc>
        <script src="https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js"> </script>
      </body>
    </html>
    """ % url_for(
        "documentation.get_yaml"
    )
    return html


@documentation.route("/documentation/spec.yaml", methods=["GET"])
def get_yaml():
    # with open("doc/karp_api_spec.yaml") as fp:
    #     spec = fp.read()
    spec = pkg_resources.resource_string(
        "karp", "data_files/karp_api_spec.yaml"
    ).decode("utf-8")
    return Response(spec, mimetype="text/yaml")


@documentation.route("/favicon.ico", methods=["GET"])
def favicon_blocker():
    return "", 404
