from typing import Any, Callable, Dict, List, Optional, TypeVar  # noqa: D100

T = TypeVar("T", bool, int, str, List[str])


def arg_get(  # noqa: D103
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


def create_field_getter(  # noqa: D103
    field: str, convert: Optional[Callable[[Any], Any]] = None
) -> Callable[[Dict], Any]:
    def getter(d: Dict):  # noqa: ANN202
        result = d[field]
        return convert(result) if convert else result

    return getter
