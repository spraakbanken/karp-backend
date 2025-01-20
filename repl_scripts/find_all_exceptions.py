# Finds all exception classes that are declared in Karp.
# To be used in future to help with cleaning up the exception hierarchy :)

import sys


def superclasses(cls):
    return [sup for sup in cls.__mro__ if cls in sup.__subclasses__()]


exception_types = set()
for module in sys.modules.values():
    if module.__name__.startswith("karp"):
        for item in module.__dict__.values():
            if isinstance(item, type) and item.__module__.startswith("karp") and issubclass(item, BaseException):
                exception_types.add(item)


def fullname(cls):
    return cls.__module__ + "." + cls.__name__


def hierarchy(cls):
    return fullname(cls) + ": " + ", ".join(map(fullname, superclasses(cls)))


def print_exception_hierarchy(cls, indent=0):
    if cls.__module__.startswith("karp"):
        if indent == 0:
            print()
            line = hierarchy(cls)
        else:
            line = fullname(cls)

        print(" " * indent + "* " + line)
        indent += 4

    for subcls in cls.__subclasses__():
        print_exception_hierarchy(subcls, indent)


print_exception_hierarchy(BaseException)
