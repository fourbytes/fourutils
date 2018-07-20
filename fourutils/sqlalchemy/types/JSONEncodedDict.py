import json
from typing import Union

from sqlalchemy.types import TypeDecorator, Text


JSONEncodable = Union[dict, list, str]


class JSONEncodedDict(TypeDecorator):
    """Represents an immutable structure as a json-encoded string."""

    impl = Text

    def process_bind_param(self, value: JSONEncodable, dialect) -> str:
        if value is not None:
            value = json.dumps(value)
        return value

    def process_result_value(self, value: str, dialect) -> JSONEncodable:
        if value is not None:
            value = json.loads(value)
        return value