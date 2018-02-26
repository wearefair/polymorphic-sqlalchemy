import collections

def namedtuple_with_defaults(typename, field_names, default_values=()):
    """
    https://stackoverflow.com/a/18348004/1497443
    """
    T = collections.namedtuple(typename, field_names)
    T.__new__.__defaults__ = (None,) * len(T._fields)
    if isinstance(default_values, collections.Mapping):
        prototype = T(**default_values)
    else:
        prototype = T(*default_values)
    T.__new__.__defaults__ = tuple(prototype)
    return T
