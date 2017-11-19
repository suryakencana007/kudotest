import uuid
from datetime import datetime, date, time
from decimal import Decimal

import sqlalchemy
from baka._compat import text_type
from sqlalchemy.ext.hybrid import HYBRID_PROPERTY


MAX_LIMIT = 100
DEFAULT_LIMIT = 10

def serialize(value):
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, time):
        return value.isoformat()
    if isinstance(value, Decimal):
        return text_type(value)
    if isinstance(value, uuid.UUID):
        return text_type(value)
    if hasattr(value, 'serialize'):
        return value.serialize()
    return value


def mapper_alchemy(model, item, expose_fields=None, primary_key=False):
    atts = {}
    fields = {}

    for key, col in sqlalchemy.inspect(model).mapper.all_orm_descriptors.items():

        if expose_fields is None or key in expose_fields:
            if col.extension_type == HYBRID_PROPERTY:
                atts[key] = col
                fields[key] = col

    for key, col in sqlalchemy.inspect(model).mapper.columns.items():
        if key == sqlalchemy.inspect(model).primary_key[0].name and not primary_key:
            continue

        if len(col.foreign_keys) > 0:
            continue

        if expose_fields is None or key in expose_fields:
            atts[key] = col
            fields[key] = col

    atts = {
        key: serialize(getattr(item, key))
        for key, val in atts.items()
    }
    return atts
