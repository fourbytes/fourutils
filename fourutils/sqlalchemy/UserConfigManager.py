import logging
from typing import Optional
from functools import wraps

import termcolor
import msgpack
from sqlalchemy.exc import SQLAlchemyError, ProgrammingError

from ..log import make_logger

try:
    from flask import request, has_app_context
except ImportError:
    request = None
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

        self.log = make_logger(__name__)
    
    @teardown_db
    def get(self, key):
        key = key.lower()
        if request:
            if not hasattr(request, 'user_config_cache'):
                request.user_config_cache = {}
            if key in request.user_config_cache:
                return request.user_config_cache[key]

        kv: Optional[self.kv_model] = None
        try:
            kv = self.session.query(self.kv_model).get(key)
        except ProgrammingError:
            self.session.rollback()

        if kv:
            # Key was found in db, good to go.
            cv = self.decode(kv.value)
            if request:
                request.user_config_cache[key] = cv
            return cv

        # Key isn't in db, check defaults.
        if key in self.defaults:
            # self.log.debug(f"Loaded default {key}: {self.defaults[key]}")
            # Got a default, return it.
            return self.defaults[key]
        elif self.strict:
            # Item wasn't previously set and doesn't have a default.
            raise KeyError
        else:
            self.log.error(f"Tried to load missing key: {key}")
            return None

    @teardown_db
    def set(self, key, value):
        key = key.lower()
        kv = self.session.query(self.kv_model).get(key)
        if not kv:
            kv = self.kv_model(key=key)
            self.session.add(kv)

        self.log.debug(f'Setting {key}: {value}')
        kv.value = self.encode(value)
        self.session.commit()

        return kv.value

    # Return a dict of all settings, including defaults.
    @teardown_db
    def get_all(self):
        return {**self.defaults, **{
            r.key: self.decode(r.value)
            for r in self.kv_model.query.all()
        }}

    # Remove the key from the db, effectively resetting to the default value.
    @teardown_db
    def reset(self, key):
        kv = self.kv_model.query.get(key)
        if kv:
            self.session.delete(kv)
            self.session.commit()

    # Encode the value before inserting into the db.
    def encode(self, value):
        return msgpack.packb(value, use_bin_type=True)

    # Decode the value from the db.
    def decode(self, value):
        return msgpack.unpackb(value, raw=False)