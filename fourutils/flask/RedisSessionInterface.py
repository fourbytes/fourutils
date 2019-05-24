import pickle
from datetime import timedelta
from uuid import uuid4

from flask.sessions import SessionInterface, SessionMixin
from redis import Redis
from werkzeug.datastructures import CallbackDict

from ..log import make_logger


class RedisSession(CallbackDict, SessionMixin):

    def __init__(self, initial=None, sid=None, new=False):
        def on_update(self):
            self.modified = True
        CallbackDict.__init__(self, initial, on_update)
        self.sid = sid
        self.new = new
        self.modified = False


class RedisSessionInterface(SessionInterface):
    serializer = pickle
    session_class = RedisSession

    def __init__(self, redis=None, prefix='session:'):
        self.log = make_logger(__name__)
        if redis is None:
            redis = Redis()
            self.log.debug('Created new redis session %s', redis)
        self.redis = redis
        self.prefix = prefix

    def generate_sid(self):
        return str(uuid4())

    def get_redis_expiration_time(self, app, session):
        if session.permanent:
            return app.permanent_session_lifetime
        return timedelta(days=1)

    def open_session(self, app, request):
        sid = request.cookies.get(app.session_cookie_name)
        if not sid:
            sid = self.generate_sid()
            self.log.debug('Opened new session %s', sid)
            return self.session_class(sid=sid, new=True)
        val = self.redis.get(self.prefix + sid)
        if val is not None:
            try:
                data = self.serializer.loads(val)
            except:
                self.log.exception('Failed to deserialize session data \
                                    for %s, opening new session.', sid)
                return self.session_class(sid=sid, new=True)
            else:
                self.log.debug('Opened existing session %s', sid)
                return self.session_class(data, sid=sid)
        self.log.debug('Opened new session %s', sid)
        return self.session_class(sid=sid, new=True)

    def save_session(self, app, session, response):
        domain = self.get_cookie_domain(app)
        if not session:
            self.log.debug('Deleting existing session %s', session.sid)
            self.redis.delete(self.prefix + session.sid)
            if session.modified:
                response.delete_cookie(app.session_cookie_name,
                                       domain=domain)
            return
        redis_exp = self.get_redis_expiration_time(app, session)
        cookie_exp = self.get_expiration_time(app, session)

        key = self.prefix + session.sid
        val = self.serializer.dumps(dict(session))

        self.redis.setex(name=key, value=val, time=int(redis_exp.total_seconds()))

        response.set_cookie(app.session_cookie_name, session.sid,
                            expires=cookie_exp, httponly=True,
                            domain=domain)
        self.log.debug('Saved session %s', session.sid)
