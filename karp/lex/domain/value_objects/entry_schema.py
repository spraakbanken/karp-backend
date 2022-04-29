import logging

import fastjsonschema

from karp.lex.domain import errors


logger = logging.getLogger(__name__)


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
                "Entry not valid", extra={"entry": json_obj, "error_message": str(e)}
            )
            raise errors.InvalidEntry() from e
