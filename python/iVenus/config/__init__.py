def loadYmlConfig(path):
    import yaml
    f = open(path)
    d = yaml.safe_load(f)
    f.close()
    return Struct(d)


class Struct:
    '''The recursive class for building and representing objects with.'''
    def __init__(self, obj):
        for k, v in obj.iteritems():
            if isinstance(v, dict):
                setattr(self, k, Struct(v))
            else:
                setattr(self, k, v)
    
    def __getitem__(self, val):
        return self.__dict__[val]
  
    def __repr__(self):
        return '{%s}' % str(', '.join('%s : %s' % (k, repr(v)) for
                                      (k, v) in self.__dict__.iteritems()))