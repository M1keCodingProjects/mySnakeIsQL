from enum      import StrEnum
from SQLDomain import SQLDomain

class CompareOp(StrEnum):
    EQUALS         = "="
    NOT_EQUALS     = "!="
    DIFFERENT      = "<>"
    GREATER_EQUALS = ">="
    LESS_EQUALS    = "<="
    GREATER        = ">"
    LESS           = "<"

    def exec[T](self, domain:SQLDomain, lhs:T, rhs:T) -> bool:
        match self:
            case CompareOp.EQUALS:                           return domain.compareEqs(lhs, rhs)
            case CompareOp.NOT_EQUALS | CompareOp.DIFFERENT: return domain.compareNeq(lhs, rhs)
            case CompareOp.GREATER_EQUALS:                   return domain.compareGre(lhs, rhs)
            case CompareOp.LESS_EQUALS:                      return domain.compareLse(lhs, rhs)
            case CompareOp.GREATER:                          return domain.compareGrt(lhs, rhs)
            case CompareOp.LESS:                             return domain.compareLst(lhs, rhs)

class Predicate[T]:
    def __init__(self, attrName:str, op:CompareOp, value:T) -> None:
        self.attrName, self.op, self.value = attrName, op, value
    
    def isSatisfied(self, domain:SQLDomain, attrValueInTable:T) -> bool:
        return self.op.exec(domain, attrValueInTable, self.value)

def main() -> None:
    pass

if __name__ == "__main__": main()