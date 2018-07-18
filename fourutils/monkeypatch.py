def patch_uuid():
    import uuid

    global StringCompareUUID
    class StringCompareUUID(uuid.UUID):
        r"""Monkeypatched UUID class so we can check them directly
        against strings for convenience, shouldn't have any weird
        side-effects."""

        def __eq__(self, obj):
            if isinstance(obj, (str, bytes,)):
                try:
                    obj = uuid.UUID(obj)
                except ValueError:
                    pass
            return super().__eq__(obj)
        
        def __hash__(self):
            return hash(self.int)

    StringCompareUUID.__name__ = uuid.UUID.__name__
    uuid.UUID = StringCompareUUID
