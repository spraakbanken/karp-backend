import pkg_resources

plugins = {}


def init():
    for entry_point in pkg_resources.iter_entry_points("karp.plugins"):
        plugins[entry_point.name] = entry_point.load()
        plugins[entry_point.name].init()
