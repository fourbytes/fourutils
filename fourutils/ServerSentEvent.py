import json


class ServerSentEvent(object):

    def __init__(self, data):
        self.data = data
        if isinstance(self.data, (dict, list)):
            self.data = json.dumps(self.data)
        self.event = None
        self.id = None
        self.desc_map = {
            'data': self.data,
            'event': self.event,
            'id': self.id
        }

    def encode(self):
        if not self.data:
            return ''

        lines = ["%s: %s" % (k, v)
                 for k, v in self.desc_map.items() if v]

        return "%s\n\n" % "\n".join(lines)
