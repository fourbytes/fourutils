import os
import importlib

from .ReverseProxied import ReverseProxied


def load_config_cls(config_module, *args, **kwargs):
    env_config_classname = os.environ.get('CONFIG_CLASS', 'Development') + 'Config'

    config_cls = getattr(importlib.import_module(config_module), env_config_classname)
    config_obj = config_cls()

    return config_obj

__all__ = ['ReverseProxied', 'load_config_cls']
