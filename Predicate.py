from enum import StrEnum

class CompareOp(StrEnum):
    EQUALS         = "="
    NOT_EQUALS     = "!="
    DIFFERENT      = "<>"
    GREATER_EQUALS = ">="
    LESS_EQUALS    = "<="
    GREATER        = ">"
    LESS           = "<"

    def exec[T](self, lhs:T, rhs:T) -> bool:
        match self:
            case CompareOp.EQUALS:
                return lhs == rhs
            
            case CompareOp.NOT_EQUALS | CompareOp.DIFFERENT:
                return lhs != rhs
            
            case CompareOp.GREATER_EQUALS:
                return lhs >= rhs
            
            case CompareOp.LESS_EQUALS:
                return lhs <= rhs
            
            case CompareOp.GREATER:
                return lhs  > rhs
            
            case CompareOp.LESS:
                return lhs  < rhs

class Predicate:
    def __init__(self, attrName:str, op:CompareOp, value:int) -> None:
        self.attrName, self.op, self.value = attrName, op, value
    
    def isSatisfied(self, attrValueInTable:int) -> bool:
        return self.op.exec(attrValueInTable, self.value)

def main() -> None:
    print(CompareOp("=").name)
    print(Predicate("", CompareOp.GREATER, 3).isSatisfied(2))
    print(Predicate("", CompareOp.GREATER, 3).isSatisfied(5))

if __name__ == "__main__": main()