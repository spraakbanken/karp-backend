import logging  # noqa: D100, I001

import fastjsonschema

from karp.lex.domain import errors


logger = logging.getLogger(__name__)


class EntrySchema:  # noqa: D101
    def __init__(self, json_schema: dict):  # noqa: D107, ANN204
        try:
            self._compiled_schema = fastjsonschema.compile(json_schema)
        except fastjsonschema.JsonSchemaDefinitionException as e:
            raise errors.InvalidEntrySchema() from e

    def validate_entry(self, json_obj: dict):  # noqa: ANN201, D102
        try:
            self._compiled_schema(json_obj)
        except fastjsonschema.JsonSchemaException as e:
            logger.warning(
                "Entry not valid", extra={"entry": json_obj, "error_message": str(e)}
            )
            raise errors.InvalidEntry() from e
