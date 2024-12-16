from typing import *

def compareCaseInsensitive(s1:str, s2:str) -> bool: return s1.lower() == s2.lower()

def formatIntoDetails(details:str, sep = ',') -> str:  return f"{sep} {details}" * bool(details)
def asPatternOpts(opts:list[str])  -> str:  return fr"({'|'.join(opts)})"
def flatten[T](l:list[list[T]]) -> list[T]: return [ item for innerList in l for item in innerList ]

def produceTableSepWithDivits(segmentSizes :list[int], divitCh, lineCh = '─') -> str:
    return divitCh.join([ lineCh * size for size in segmentSizes ])

class CustomErr(Exception):
    MSG = ""
    def __init__(self, msg = "") -> None: super().__init__(self.MSG + formatIntoDetails(msg) + '.')
    def __str__(self) -> str: return f"{self.__class__.__name__}: {super().__str__()}"

class BaseClassErr(CustomErr):
    MSG = "Forbidden direct usage of base class"
    CLASS_NAME = ""
    def __init__(self, methodName:str) -> None:
        super().__init__(f"cannot call method \"{methodName}\" on an instance of {self.CLASS_NAME}")

class Res[T, E:Exception]:
    def __init__(self, *, value:T|None, err:E|None) -> None:
        """ Private Constructor """
        self.value, self.err = value, err
    
    def Ok(value :T|None = None) -> Self:
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
    
    def mapErr[E2:Exception](self, mapper:Callable[[E], E2]) -> "Res[T, E2]":
        """ This method panics when the mapper does. """
        return self if self.isOk() else Res.Err(mapper(self.err))

    def flatten(self:"Res[Res[T, E], E]") -> "Res[T, E]":
        return self if self.isErr() or not isinstance(self.value, Res) else self.value
    
    def flatMap[U](self, mapper:Callable[[T], U]) -> "Res[U, E]":
        return self.map(mapper).flatten()

    def toOverallList(seq:list["Res[T, E]"]) -> "Res[list[T], E]":
        """ Static """
        successes :list[T] = []
        for res in seq:
            if res.isErr(): return res
            successes.append(res.value)
        
        return Res.Ok(successes)

    def toOverallDict[K](seq:dict[K, "Res[T, E]"]) -> "Res[dict[K, T], E]":
        """ Static """
        successes :dict[K, Res[T, E]] = {}
        for k, res in seq.items():
            if res.isErr(): return res
            successes[k] = res.value
        
        return Res.Ok(successes)

    def __repr__(self) -> str:
        variant, content = ("Ok", self.value) if self.isOk() else ("Err", self.err)
        return f"Result::{repr(variant)}({repr(content)})"

def main() -> None:
    pass

if __name__ == "__main__": main()