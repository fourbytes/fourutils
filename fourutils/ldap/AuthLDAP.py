from logging import WARN, DEBUG, INFO
from enum import Enum

import ldap3
from ldap3 import Connection, Server, ServerPool
from sentry_sdk import add_breadcrumb

from ..log import make_logger


class AuthLDAPResult(Enum):
    CONNECTION_FAILED_UNKNOWN = 1
    AUTH_FAILED = 2
    SUCCESS = 3
    BIND_USER_AUTH_FAILED = 4


class AuthLDAP(object):
    def __init__(self, app, config_obj=None, init_config=True):
        self.app = app
        self.log = make_logger(
            __name__, level=DEBUG if self.app.debug else INFO)

        def log_exception(txt, **kwargs):
            return self.log.error(txt, exc_info=True, **kwargs)
        self.handle_exception = log_exception

        if init_config:
            self.init_config(config_obj=config_obj)

    def init_config(self, config_obj=None):
        if not config_obj:
            config_obj = self.app.config
        self.log.info(f"Initialising LDAP settings from <{config_obj.__module__}.{type(config_obj).__name__}>")
        self.use_ldap = config_obj.get('ENABLE_LDAP')
        if self.use_ldap:
            ldap_host = config_obj.get('LDAP_HOST')
            ldap_port = config_obj.get('LDAP_PORT')
            self.base_dn = config_obj.get('LDAP_BASE_DN')
            self.id_attribute = config_obj.get('LDAP_USER_LOGIN_ATTR')

            if ldap_host and ldap_port:
                self._server = Server('{}:{}'.format(ldap_host, ldap_port),
                                      get_info=ldap3.ALL)

            self.log.info(f"Using LDAP server: {ldap_host}:{ldap_port}")
        else:
            self.log.info('LDAP is disabled.')

    def get_user_info(self, username, connection):
        # Using a bound connection, we will go fetch some LDAP attributes
        # for the user that logged in.
        connection.search(
            search_base=self.base_dn,
            search_filter='({}={})'.format(
                self.id_attribute, username),
            search_scope=ldap3.SUBTREE,
            attributes=[ldap3.ALL_ATTRIBUTES, ldap3.ALL_OPERATIONAL_ATTRIBUTES]
        )

        add_breadcrumb(
            category='ldap_auth',
            data=connection.response,
            level='debug',
        )

        filtered_response = [x for x in connection.response if 'dn' in x]

        if len(filtered_response) < 1:
            # Found no results
            self.log.error(f"Received invalid LDAP response, expected 1 got none: {connection.response} for username {username}")
            return None
        elif len(filtered_response) > 1:
            self.log.error(f"Received invalid LDAP response, expected 1 got {len(filtered_response)}: {filtered_response} for username {username}")
            return None

        return connection.response[0]

    def authenticate(self, username, password):
        if not self.use_ldap:
            return AuthLDAPResult.AUTH_FAILED, None

        connection = Connection(
            self._server,
            user=f'detnsw\\{username}',
            password=password,
            authentication=ldap3.NTLM,
            raise_exceptions=True,
            read_only=True,
            client_strategy=ldap3.RESTARTABLE
        )

        num_retries = self.app.config.get('LDAP_NUM_RETRY', 3)
        for _ in range(0, num_retries):
            try:
                connection.bind()
                user_data = self.get_user_info(username, connection)
                self.log.debug(
                    f"Authentication succeeded for user {repr(username)}")
            except ldap3.core.exceptions.LDAPInvalidCredentialsResult:
                self.log.info(
                    f"Authentication failed for user {repr(username)}")
                return AuthLDAPResult.AUTH_FAILED, None
            except ldap3.core.exceptions.LDAPCommunicationError as e:
                self.handle_exception(
                    f"Authentication failed due to LDAPCommunicationError: {connection.last_error}")
            except (ldap3.core.exceptions.LDAPServerPoolExhaustedError,
                    ldap3.core.exceptions.LDAPMaximumRetriesError) as e:
                self.handle_exception(
                    f"Authentication failed due to bad connection to LDAP server: {e}")
            else:
                # Successfully authenticated.
                if user_data:
                    return AuthLDAPResult.SUCCESS, user_data

                self.log.exception(
                    f"We should not have gotten here. user_data is invalid ({user_data}), check your search dn?")
                break
            finally:
                try:
                    connection.sasl_in_progress = False
                    connection.unbind()
                except:  # noqa
                    self.handle_exception("Unknown exception.")

        self.log.exception(
            f"We should not have gotten here either. Failed after {num_retries} retries.")
        return AuthLDAPResult.CONNECTION_FAILED_UNKNOWN, None

    @property
    def connection_established(self):
        if not self.use_ldap:
            return False

        connection = Connection(self._server, raise_exceptions=True, read_only=True)
        try:
            connection.bind()
        except ldap3.core.exceptions.LDAPSocketOpenError:
            return False
        except ldap3.core.exceptions.LDAPServerPoolExhaustedError:
            return False
        except ldap3.core.exceptions.LDAPOperationsErrorResult:
            return True
        except ldap3.core.exceptions.LDAPInvalidCredentialsResult:
            return True

        return True
