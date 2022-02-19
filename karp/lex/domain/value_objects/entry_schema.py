import fastjsonschema

from karp.lex.domain import errors


class EntrySchema:
    def __init__(self, json_schema: dict):
        try:
            self._compiled_schema = fastjsonschema.compile(json_schema)
        except fastjsonschema.JsonSchemaDefinitionException as e:
            raise errors.InvalidEntrySchema() from e

    def validate_entry(self, json_obj: dict):
        try:
            self._compiled_schema(json_obj)
        except fastjsonschema.JsonSchemaException as e:
            logger.warning(
                "Entry not valid:\n{entry}\nMessage: {message}".format(
                entry=json.dumps(json_obj, indent=2), message=e.message
                )
            )
            raise errors.InvalidEntry() from e
