from typing import Dict, List, Callable, Optional, TypeVar


T = TypeVar("T", bool, int, str, List[str])


def arg_get(
    args: Dict,
    arg_name: str,
    convert: Optional[Callable[[str], T]] = None,
    default: Optional[T] = None,
) -> Optional[T]:
    arg = args.get(arg_name, None)
    if arg is None:
        return default
    if convert is None:
        return arg
    return convert(arg)
