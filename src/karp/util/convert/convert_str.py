from typing import List, Callable


def str2list(delimiter: str = None) -> Callable[[str], List[str]]:
    def result(x: str) -> List[str]:
        return x.split(delimiter)
    return result
