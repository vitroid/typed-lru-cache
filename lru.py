from collections import OrderedDict
from collections.abc import Callable
from typing import Final, Generic, Hashable, NamedTuple, Optional, ParamSpec, TypeVar

T = TypeVar("T")
P = ParamSpec("P")


class CacheInfo(NamedTuple):
    hits: int
    misses: int
    maxsize: int
    currsize: int


class LruCache(Generic[T]):
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.__cache: OrderedDict[Hashable, T] = OrderedDict()

    def get(self, key: Hashable) -> Optional[T]:
        if key not in self.__cache:
            return None
        self.__cache.move_to_end(key)
        return self.__cache[key]

    def insert(self, key: Hashable, value: T) -> None:
        if len(self.__cache) == self.capacity:
            self.__cache.popitem(last=False)
        self.__cache[key] = value
        self.__cache.move_to_end(key)

    def __len__(self) -> int:
        return len(self.__cache)

    def clear(self) -> None:
        self.__cache.clear()


class _LruCacheFunctionWrapper(Generic[P, T]):
    def __init__(self, func: Callable[P, T], maxsize: int):
        self.__wrapped__ = func
        self.__cache = LruCache[T](capacity=maxsize)
        self.__hits = 0
        self.__misses = 0
        self.__maxsize: Final = maxsize

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> T:

        call_args = args + tuple(kwargs.items())

        ret = self.__cache.get(call_args)

        if ret is None:
            self.__misses += 1
            ret = self.__wrapped__(*args, **kwargs)
            self.__cache.insert(call_args, ret)
        else:
            self.__hits += 1

        return ret

    def cache_info(self) -> CacheInfo:
        return CacheInfo(
            hits=self.__hits,
            misses=self.__misses,
            currsize=len(self.__cache),
            maxsize=self.__maxsize,
        )

    def cache_clear(self) -> None:
        self.__cache.clear()
        self.__hits = 0
        self.__misses = 0

    @property
    def cache(self) -> LruCache[T]:
        return self.__cache


def lru_cache(maxsize: int) -> Callable[[Callable[P, T]], _LruCacheFunctionWrapper[P, T]]:
    def decorator(func: Callable[P, T]) -> _LruCacheFunctionWrapper[P, T]:
        wrapped = _LruCacheFunctionWrapper(func, maxsize)
        wrapped.__doc__ = func.__doc__
        return wrapped

    return decorator
