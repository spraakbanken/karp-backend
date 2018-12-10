
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
