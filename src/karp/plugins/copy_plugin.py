"""A plugin that just copies a value given as a parameter.

Useful mainly for testing the plugin system."""

from .plugin import Plugin


class CopyPlugin(Plugin):
    def output_config(self, config):  # noqa
        return config

    def generate(self, config, value):
        return value
