from collections import OrderedDict
from collections.abc import Callable
from typing import Final, Generic, Hashable, NamedTuple, Optional, ParamSpec, TypeVar
from logging import getLogger

T = TypeVar("T")
P = ParamSpec("P")


# LRUのないただの無制限キャッシュ。これをディスク上に実装すればいい。
class _CacheFunctionWrapper(Generic[P, T]):
    def __init__(self, func: Callable[P, T]):
        self.__wrapped__ = func
        self.__cache = dict()

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> T:

        call_args = args + tuple(kwargs.items())

        if call_args not in self.__cache:
            ret = self.__wrapped__(*args, **kwargs)
            self.__cache[call_args] = ret
        else:
            ret = self.__cache[call_args]
        return ret

    @property
    def cache(self) -> dict:
        return self.__cache


def cache() -> Callable[[Callable[P, T]], _CacheFunctionWrapper[P, T]]:
    def decorator(func: Callable[P, T]) -> _CacheFunctionWrapper[P, T]:
        wrapped = _CacheFunctionWrapper(func)
        wrapped.__doc__ = func.__doc__
        return wrapped

    return decorator

@cache()
def fib(n):
    return 1 if n in (0, 1) else fib(n - 1) + fib(n - 2)

if __name__ == "__main__":
    print(fib(40))
