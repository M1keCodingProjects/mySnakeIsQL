from typing   import *
from datetime import *
from Utils    import formatIntoDetails, CustomErr, BaseClassErr, Res

class SQLDomain[T]:
    class BCE(BaseClassErr): CLASS_NAME   = "SQLDomain"
    class DomainSyntaxErr(CustomErr): MSG = "Couldn't parse string as valid domain"
    class DomainValueErr(CustomErr):
        MSG = "Failed to parse value into expected domain type"
        def __init__(self, domain:"SQLDomain", value, details = "") -> None:
            super().__init__(f"could not parse \"{value}\" into {domain.TYPE} domain type" + formatIntoDetails(details))

    TYPE = "default"
    def __init__(self, name:str) -> None:
        self.name = name

    def canValidate(self, value:T) -> bool:
        raise SQLDomain.BCE("canValidate")

    def parseValue(self, valueStr:str) -> Res[T, BCE]:
        raise SQLDomain.BCE("parseValue")
    
    def compareEqs(self, lhs:T, rhs:T) -> bool:
        return lhs == rhs
    
    def compareNeq(self, lhs:T, rhs:T) -> bool:
        return lhs != rhs
    
    def compareGre(self, lhs:T, rhs:T) -> bool:
        return lhs >= rhs
    
    def compareLse(self, lhs:T, rhs:T) -> bool:
        return lhs <= rhs
    
    def compareGrt(self, lhs:T, rhs:T) -> bool:
        return lhs > rhs
    
    def compareLst(self, lhs:T, rhs:T) -> bool:
        return lhs < rhs
    
    def __repr__(self) -> str:
        return f"{self.name} : {self.TYPE}"
    
    def copy(self) -> Self:
        return self.__class__(self.name)
        # This will panic if called on the base class, otherwise it provides a useful argless copy that can
        # be inherited directly by subclasses that don't hold any data.

def parseDomain(name:str, dType:str) -> Res[SQLDomain, SQLDomain.DomainSyntaxErr]:
    # TODO: rework with a builder or an automatic class.NAME -> class mapping because this introduces
    # heavy needless repetition and shaky responsibilities.
    if dType == DateDomain.TYPE:    return Res.Ok(DateDomain(name))
    if dType == IntegerDomain.TYPE: return Res.Ok(IntegerDomain(name))

    if (lparenPos := dType.find('(')) == -1:
        return Res.Err(SQLDomain.DomainSyntaxErr(f"cannot recognize \"{dType}\" as any valid domain"))

    if dType[-1] != ')': return Res.Err(SQLDomain.DomainSyntaxErr(f"unclosed parentheses in \"{dType}\""))

    domainKw = dType[:lparenPos]
    if domainKw == StringDomain.TYPE:
        return Res.wrap(int, dType[lparenPos + 1:-1]
        ).map(   lambda ml       : StringDomain(name, ml)
        ).mapErr(lambda valueErr : SQLDomain.DomainSyntaxErr(
            f"varchar domain expected integer \"maxLenght\" argument, {valueErr}"))

class IntegerDomain(SQLDomain[int]):
    TYPE = "integer"
    def canValidate(self, value:int) -> bool:
        return isinstance(value, int)

    def parseValue(self, valueStr:str) -> Res[int, SQLDomain.DomainValueErr]:
        return Res.wrap(int, valueStr).mapErr(
            lambda valueErr : SQLDomain.DomainValueErr(self, valueStr, str(valueErr)))

class StringDomain(SQLDomain[str]):
    TYPE = "varchar"
    def __init__(self, name:str, maxLen:int) -> None:
        super().__init__(name)
        self.maxLen = maxLen
    
    def isWithinMaxLen(self, value:str) -> bool:
        return len(value) <= self.maxLen

    def canValidate(self, value:str) -> bool:
        return isinstance(value, str) and self.isWithinMaxLen(value)
    
    def parseValue(self, valueStr:str) -> Res[str, SQLDomain.DomainValueErr]:
        return Res.Ok(valueStr) if self.isWithinMaxLen(valueStr) else Res.Err(
            SQLDomain.DomainValueErr(self, valueStr, f"value exceeds max length ({self.maxLen})"))
    
    def compareEqs(self, lhs:str, rhs:str) -> bool:
        return super().compareEqs(lhs.lower(), rhs.lower())

    def compareNeq(self, lhs:str, rhs:str) -> bool:
        return super().compareNeq(lhs.lower(), rhs.lower())
    
    def compareGre(self, lhs:str, rhs:str) -> bool:
        return super().compareGre(lhs.lower(), rhs.lower())
    
    def compareLse(self, lhs:str, rhs:str) -> bool:
        return super().compareLse(lhs.lower(), rhs.lower())
    
    def compareGrt(self, lhs:str, rhs:str) -> bool:
        return super().compareGrt(lhs.lower(), rhs.lower())
    
    def compareLst(self, lhs:str, rhs:str) -> bool:
        return super().compareLst(lhs.lower(), rhs.lower())
    
    def __repr__(self) -> str:
        return super().__repr__() + f"({self.maxLen})"

    def copy(self) -> Self:
        return StringDomain(self.name, self.maxLen)

class DateDomain(SQLDomain[datetime]):
    TYPE = "date"
    def canValidate(self, value:datetime) -> bool:
        return isinstance(value, datetime)

    def parseDate(valueStr:str) -> Res[datetime, Exception]:
        """Static"""
        return Res.wrap(datetime.strptime, valueStr, "%d/%m/%Y")
    
    def parseValue(self, valueStr:str) -> Res[datetime, SQLDomain.DomainValueErr]:
        return DateDomain.parseDate(valueStr).mapErr(
            lambda valueErr : SQLDomain.DomainValueErr(self, valueStr, str(valueErr)))

def main() -> None:
    print(DateDomain("BirthDate"))

if __name__ == "__main__": main()