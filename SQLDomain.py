from typing   import *
from datetime import *
from Utils    import formatIntoDetails, CustomErr, BaseClassErr, Res

class SQLDomain[T]:
    class BCE(BaseClassErr): CLASS_NAME   = "SQLDomain"
    class DomainSyntaxErr(CustomErr): MSG = "Couldn't parse string as valid domain"
    class DomainValueErr(CustomErr):
        MSG = "Failed to parse value into expected domain type"
        def __init__(self, domain:"SQLDomain", value, details = "") -> None:
            super().__init__(f"could not parse \"{value}\" into {domain} domain type" + formatIntoDetails(details))

    NAME = "default"
    def __init__(self) -> None:
        raise SQLDomain.BCE("constructor")

    def canValidate(self, value:T) -> bool:
        raise SQLDomain.BCE("canValidate")

    def parseValue(self, valueStr:str) -> Res[T, BCE]:
        raise SQLDomain.BCE("parseValue")
    
    def __repr__(self) -> str:
        return self.NAME
    
    def copy(self) -> Self:
        return self.__class__()
        # This will panic if called on the base class, otherwise it provides a useful argless copy that can
        # be inherited directly by subclasses that don't hold any data.

def parseDomain(domainStr:str) -> Res[SQLDomain, SQLDomain.DomainSyntaxErr]:
    # TODO: rework with a builder or an automatic class.NAME -> class mapping because this introduces
    # heavy needless repetition and shaky responsibilities.
    if domainStr == IntegerDomain.NAME: return Res.Ok(IntegerDomain())
    if domainStr == DateDomain.NAME:    return Res.Ok(DateDomain())

    if (lparenPos := domainStr.find('(')) == -1:
        return Res.Err(SQLDomain.DomainSyntaxErr(f"cannot recognize \"{domainStr}\" as any valid domain"))

    if domainStr[-1] != ')': return Res.Err(SQLDomain.DomainSyntaxErr(f"unclosed parentheses in \"{domainStr}\""))

    domainKw = domainStr[:lparenPos]
    if domainKw == StringDomain.NAME:
        return Res.wrap(int, domainStr[lparenPos + 1:-1]
        ).map(   lambda ml       : StringDomain(ml)
        ).mapErr(lambda valueErr : SQLDomain.DomainSyntaxErr(
            f"varchar domain expected integer \"maxLenght\" argument, {valueErr}"))

class IntegerDomain(SQLDomain[int]):
    NAME = "integer"
    def __init__(self) -> None: pass
    def canValidate(self, value:int) -> bool:
        return isinstance(value, int)

    def parseValue(self, valueStr:str) -> Res[int, SQLDomain.DomainValueErr]:
        return Res.wrap(int, valueStr).mapErr(
            lambda valueErr : SQLDomain.DomainValueErr(self, valueStr, str(valueErr)))

class StringDomain(SQLDomain[str]):
    NAME = "varchar"
    def __init__(self, maxLen:int) -> None:
        self.maxLen = maxLen
    
    def isWithinMaxLen(self, value:str) -> bool:
        return len(value) <= self.maxLen

    def canValidate(self, value:str) -> bool:
        return isinstance(value, str) and self.isWithinMaxLen(value)
    
    def parseValue(self, valueStr:str) -> Res[str, SQLDomain.DomainValueErr]:
        return Res.Ok(valueStr.upper()) if self.isWithinMaxLen(valueStr) else Res.Err(
            SQLDomain.DomainValueErr(self, valueStr, f"value exceeds max length ({self.maxLen})"))
    
    def __repr__(self) -> str:
        return super().__repr__() + f"({self.maxLen})"

    def copy(self) -> Self:
        return StringDomain(self.maxLen)

class DateDomain(SQLDomain[datetime]):
    NAME = "date"
    def __init__(self) -> None: pass
    def canValidate(self, value:datetime) -> bool:
        return isinstance(value, datetime)

    def parseValue(self, valueStr:str) -> Res[datetime, SQLDomain.DomainValueErr]:
        return Res.wrap(datetime.strptime, valueStr, "%d/%m/%Y").mapErr(
            lambda valueErr : SQLDomain.DomainValueErr(self, valueStr, str(valueErr)))

def main() -> None:
    pass

if __name__ == "__main__": main()