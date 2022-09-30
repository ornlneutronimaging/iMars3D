# JSON schema. Cut be here or in its own file
schema = {}


class JSONValid:
    def __init__(self, schema):
        self._schema = schema

    def __get__(self, obj, objtype=None):
        return obj._json

    def __set__(self, obj, json):
        self._validate(json)
        obj._json = json

    def _validate(self, json):
        r"""check input json against class variable schema"""
        assert self._schema
        assert json
        return True
