
class KarpError(Exception):

    def __init__(self, message):
        super().__init__(message)
        self.message = message


class ResourceNotFoundError(KarpError):

    def __init__(self, resource_id, version=None):
        super().__init__('Resource not found. ID: {resource_id}, version: {version}'. format(
            resource_id=resource_id,
            version=version
        ))


class EntryNotFoundError(KarpError):

    def __init__(self, resource_id, entry_id, entry_version=None, resource_version=None):
        msg = 'Entry {entry_id} (version {entry_version}) not found. ID: {resource_id}, version: {resource_version}'
        super().__init__(msg. format(
            resource_id=resource_id,
            resource_version=resource_version if resource_version else 'latest',
            entry_id=entry_id,
            entry_version=entry_version if entry_version else 'latest'
        ))
