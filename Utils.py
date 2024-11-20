from typing import *

def flatten[T](l:list[list[T]]) -> list[T]: return [ item for innerList in l for item in innerList ]

def produceTableSepWithDivits(segmentSizes :list[int], divitCh = '┬', lineCh = '─') -> str:
    return divitCh.join([ lineCh * size for size in segmentSizes ])

class CustomErr(Exception):
    MSG = ""
    def __init__(self, msg = ""): super().__init__(f"{self.MSG}. {msg}.")

class Res[T, E:Exception]:
    def __init__(self, *, value: T | None, err: E | None) -> None:
        """ Private Constructor """
        self.value, self.err = value, err
    
    def Ok(value:T) -> Self:
        """ Public Constructor """
        return Res(value = value, err = None)
    
    def Err(err:E) -> Self:
        """ Public Constructor """
        return Res(value = None,  err = err)

    def isOk(self)  -> bool: return self.err is None
    def isErr(self) -> bool: return self.err is not None

    # This cannot be typed better because python bad.
    def wrap(fn:Callable[..., T], *args) -> Self:
        """ Static """
        try: return Res.Ok(fn(*args))
        except Exception as e: return Res.Err(e)
    
    def unwrap(self, customErr :Exception | None = None) -> T:
        if self.isErr(): raise customErr or self.err
        return self.value
    
    def unwrapOr(self, default:T) -> T: return self.value if self.isOk() else default

    def map[U](self, mapper:Callable[[T], U]) -> "Res[U, E]":
        return self if self.isErr() else Res.wrap(mapper, self.value)
    
    def flatten(self:"Res[Res[T, E], E]") -> "Res[T, E]":
        return self if self.isErr() or not isinstance(self.value, Res) else self.value
    
    def flatMap[U](self, mapper:Callable[[T], U]) -> "Res[U, E]":
        return self.map(mapper).flatten()