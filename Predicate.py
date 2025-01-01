from typing    import *
from datetime  import datetime
from enum      import StrEnum
from SQLDomain import SQLDomain

class Attribute:
    def __init__(self, name:str) -> None:
        self.name = name

    def __repr__(self) -> str:
        return self.name

MAX_PRIORITY = 2 # This should be inside MathOp but Python bad so I can't (conveniently)
class MathOp(StrEnum):
    ADD = "+"
    SUB = "-"
    MUL = "*"
    DIV = "/"
    MOD = "%"

    def getPriority(self) -> int:
        match self:
            case MathOp.ADD | MathOp.SUB: return 0
            case MathOp.MOD             : return 1
            case MathOp.MUL | MathOp.DIV: return MAX_PRIORITY

    def hasPriorityOver(self, other:Self) -> bool:
        return self.getPriority() > other.getPriority()

    def exec[T](self, domain:SQLDomain, lhs:T, rhs:T) -> T:
        match self:
            case MathOp.ADD: return domain.add(lhs, rhs)
            case MathOp.SUB: return domain.sub(lhs, rhs)
            case MathOp.MUL: return domain.mul(lhs, rhs)
            case MathOp.DIV: return domain.div(lhs, rhs)
            case MathOp.MOD: return domain.mod(lhs, rhs)

type Literal = int|str|datetime
type Operand = Literal|Attribute|MathExpr
class MathExpr:
    def __init__(self, lhs:Operand, op:Optional[MathOp] = None, rhs:Optional[Operand] = None) -> None:
        self.lhs, self.op, self.rhs = lhs, op, rhs

    def _repr(item:Attribute|Literal|Self, indents :int, *, isLeftSide = False) -> str:
        return item.__repr__(indents, isLeftSide = isLeftSide) if isinstance(item, MathExpr) else item.__repr__()

    def __repr__(self, indents = 0, *, isLeftSide = False) -> str:
        leftPadding  = " " + "   " * (indents - 1)
        leftPadding += "│  " if isLeftSide else "   " * (indents > 0)
        
        tree  = f"({self.op})"
        tree += f"\n{leftPadding}├─" + MathExpr._repr(self.lhs, indents + 1, isLeftSide = True)
        tree += f"\n{leftPadding}└─" + MathExpr._repr(self.rhs, indents + 1)
        return tree

class CompareOp(StrEnum):
    EQUALS         = "="
    NOT_EQUALS     = "!="
    DIFFERENT      = "<>"
    GREATER_EQUALS = ">="
    LESS_EQUALS    = "<="
    GREATER        = ">"
    LESS           = "<"

    def exec[T](self, domain:SQLDomain[T], lhs:T, rhs:T) -> bool:
        match self:
            case CompareOp.EQUALS:                           return domain.compareEqs(lhs, rhs)
            case CompareOp.NOT_EQUALS | CompareOp.DIFFERENT: return domain.compareNeq(lhs, rhs)
            case CompareOp.GREATER_EQUALS:                   return domain.compareGre(lhs, rhs)
            case CompareOp.LESS_EQUALS:                      return domain.compareLse(lhs, rhs)
            case CompareOp.GREATER:                          return domain.compareGrt(lhs, rhs)
            case CompareOp.LESS:                             return domain.compareLst(lhs, rhs)

class CompareExpr:
    def __init__(self, lhs:MathExpr, op:CompareOp, rhs:MathExpr) -> None:
        self.lhs, self.op, self.rhs = lhs, op, rhs

class LogicOp(StrEnum):
    OR  = "or"
    AND = "and"

    def exec[T](self, domain:SQLDomain, lhs:T, rhs:T) -> bool:
        match self:
            case LogicOp.OR: return domain.logicOr(lhs, rhs)
            case LogicOp.AND: return domain.logicAnd(lhs, rhs)

class Predicate[T]:
    def __init__(self, attr:Attribute, op:CompareOp, value:T) -> None:
        self.attr, self.op, self.value = attr, op, value
    
    def isSatisfied(self, domain:SQLDomain[T], attrValueInTable:T) -> bool:
        return self.op.exec(domain, attrValueInTable, self.value)

def main() -> None:
    # a + (((b * c) / d) % e) - (f % (g * h)) + i
    e = MathExpr(Attribute("a"), MathOp.ADD, Attribute("b"))
    print(e)

if __name__ == "__main__": main()