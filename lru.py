from collections import OrderedDict
from collections.abc import Callable
from typing import Final, Generic, Hashable, NamedTuple, Optional, ParamSpec, TypeVar
from logging import getLogger

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


# sqlitedict cache
import sqlitedict
import json


class _SQLiteDictCacheFunctionWrapper(Generic[P, T]):
    def __init__(self, func: Callable[P, T], basename: str):
        self.__wrapped__ = func
        self.__basename = basename

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> T:
        logger = getLogger()
        call_args = json.dumps(args + tuple(kwargs.items()))
        logger.debug(call_args)
        with sqlitedict.open(f"{self.__basename}.sqlite") as shelf:
            if call_args not in shelf:
                ret = self.__wrapped__(*args, **kwargs)
                shelf[call_args] = ret
                shelf.commit()
            else:
                ret = shelf[call_args]
        return ret


def sqlitedict_cache(basename: str) -> Callable[[Callable[P, T]], _SQLiteDictCacheFunctionWrapper[P, T]]:
    def decorator(func: Callable[P, T]) -> _SQLiteDictCacheFunctionWrapper[P, T]:
        wrapped = _SQLiteDictCacheFunctionWrapper(func, basename)
        wrapped.__doc__ = func.__doc__
        return wrapped

    return decorator
