from collections import OrderedDict
from collections.abc import Callable
from typing import Final, Generic, Hashable, NamedTuple, Optional, ParamSpec, TypeVar
from logging import getLogger

T = TypeVar("T")
P = ParamSpec("P")


# shelves cache
import shelve
import json


class _ShelfCacheFunctionWrapper(Generic[P, T]):
    def __init__(self, func: Callable[P, T], basename: str):
        self.__wrapped__ = func
        self.__basename = basename

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> T:
        logger = getLogger()
        call_args = json.dumps(args + tuple(kwargs.items()))
        logger.debug(call_args)
        with shelve.open(f"{self.__basename}.shelf") as shelf:
            if call_args not in shelf:
                ret = self.__wrapped__(*args, **kwargs)
                shelf[call_args] = ret
            else:
                ret = shelf[call_args]
        return ret


def shelf_cache(basename: str) -> Callable[[Callable[P, T]], _ShelfCacheFunctionWrapper[P, T]]:
    def decorator(func: Callable[P, T]) -> _ShelfCacheFunctionWrapper[P, T]:
        wrapped = _ShelfCacheFunctionWrapper(func, basename)
        wrapped.__doc__ = func.__doc__
        return wrapped

    return decorator

@shelf_cache("fib")
def fib(n):
    return 1 if n in (0, 1) else fib(n - 1) + fib(n - 2)

if __name__ == "__main__":
    print(fib(40))
