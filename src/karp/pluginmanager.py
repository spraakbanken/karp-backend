import pkg_resources

plugins = {}


def init():
    # pipenv run install ../karp-tng-backend-pextract
    # pipenv run install ../paradigmextract
    # make sure to have a saldom_1.paradigms file (see karp-tng-backend-pextract)
    # see karp-tng-backend-pextract setup.py for entry_points definition

    for entry_point in pkg_resources.iter_entry_points('karp.plugins'):
        plugins[entry_point.name] = entry_point.load()

    # Now it is possible to call plugins['karppextract'].create_resource(...) etc.
