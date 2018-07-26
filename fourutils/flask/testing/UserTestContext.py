from contextlib import ContextDecorator
from unittest.mock import patch

from flask import Flask, current_app, _request_ctx_stack
from flask_login import UserMixin, current_user, login_user, logout_user


class UserTestContext(ContextDecorator):
    r"""A context manager that executes a block of code within
    the context of a specific logged in user.
    Can also be used as a decorator."""

    def __init__(self, user: UserMixin, app: Flask = False):
        self.user = user
        self.app = app or current_app
        self.client = self.app.test_client()
    
    def __enter__(self):
        # Enter the flask test client context.
        client = self.client.__enter__()

        # Run the standard login method.
        with client.session_transaction() as session:
            # A hack so that login_user sees the correct session to modify.
            with patch('flask._request_ctx_stack.top.session', new=session):
                login_user(self.user, force=True, fresh=True)

        return client

    def __exit__(self, exc_type, exc_value, tb):
        try:
            # Logout of our user gracefully.
            with self.client.session_transaction() as session:
                with patch('flask._request_ctx_stack.top.session', new=session):
                    logout_user()
        finally:
            # Exit the flask test client context.
            #self.session_transaction.__exit__(exc_type, exc_value, tb)
            self.client.__exit__(exc_type, exc_value, tb)
