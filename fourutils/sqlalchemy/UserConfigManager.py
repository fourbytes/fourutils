import logging
from typing import Optional
from functools import wraps

import msgpack
from sqlalchemy.exc import SQLAlchemyError, ProgrammingError

from ..log import make_logger

try:
    from flask import has_app_context
except ImportError:
    def has_app_context():
        return False


def teardown_db(f):
    @wraps(f)
    def wrapper(self, *args, **kwds):
        try:
            result = f(self, *args, **kwds)
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e
        if not has_app_context():
            self.log.debug('Closing session manually as we\'re outside of app context.')
            self.session.remove()
        return result
    return wrapper


class UserConfigManager(object):
    def __init__(self, session, kv_model, defaults={}, strict=True):
        self.kv_model = kv_model
        self.session = session
        self.defaults = defaults
        self.strict = strict
        self.cache = {}

        self.log = make_logger(__name__)
    
    @teardown_db
    def get(self, key):
        key = key.lower()
        if key in self.cache:
            self.log.debug(f"Loaded db_config key from cache: {key}={self.cache[key]}")
            return self.cache[key]

        kv: Optional[self.kv_model] = None
        try:
            kv = self.session.query(self.kv_model).get(key)
        except ProgrammingError:
            self.session.rollback()

        if kv:
            # Key was found in db, good to go.
            cv = self.decode(kv.value)
            self.cache[key] = cv
            return cv

        # Key isn't in db, check defaults.
        if key in self.defaults:
            self.log.debug(f"Loaded db_config key from defaults: {key}={self.defaults[key]}")
            # Got a default, return it.
            return self.defaults[key]
        elif self.strict:
            # Item wasn't previously set and doesn't have a default.
            raise KeyError
        else:
            self.log.error(f"Tried to load missing db_config key: {key}")
            return None

    @teardown_db
    def set(self, key, value):
        key = key.lower()
        kv = self.session.query(self.kv_model).get(key)
        if not kv:
            kv = self.kv_model(key=key)
            self.session.add(kv)

        kv.value = self.encode(value)
        self.session.commit()

        self.log.debug(f'Wrote db_config key to database: {key}={value}')
        self.cache[kv.key] = value

        return kv.value

    # Return a dict of all settings, including defaults.
    @teardown_db
    def get_all(self):
        self.cache = {
            r.key: self.decode(r.value)
            for r in self.kv_model.query.all()
        }
        return {**self.defaults, **self.cache}

    # Remove the key from the db, effectively resetting to the default value.
    @teardown_db
    def reset(self, key):
        kv = self.kv_model.query.get(key)
        if kv:
            self.session.delete(kv)
            self.session.commit()
        self.cache.pop(key, None)
        self.log.debug(f'Reset db_config key ({key}).')

    # Encode the value before inserting into the db.
    def encode(self, value):
        return msgpack.packb(value, use_bin_type=True)

    # Decode the value from the db.
    def decode(self, value):
        return msgpack.unpackb(value, raw=False)
