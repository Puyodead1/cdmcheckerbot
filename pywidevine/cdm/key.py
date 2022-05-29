class Key:
    def __init__(self, kid, type, key, permissions=[]):
        self.kid = kid.hex() if isinstance(kid, bytes) else kid
        self.type = type
        self.key = key.hex() if isinstance(key, bytes) else key
        self.permissions = permissions

    def to_str(self):
        return "--key {}:{}".format(self.kid, self.key)

    def __repr__(self):
        if self.type == "OPERATOR_SESSION":
            return "key(kid={}, type={}, key={}, permissions={})".format(self.kid, self.type, self.key, self.permissions)
        else:
            return "key(kid={}, type={}, key={})".format(self.kid, self.type, self.key)
