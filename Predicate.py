from typing    import *
from datetime  import datetime
from enum      import StrEnum
from SQLDomain import SQLDomain

class Attribute:
    def __init__(self, name:str) -> None:
        self.name = name

    def __repr__(self) -> str:
        return self.name

class MathOp(StrEnum):
    ADD = "+"
    SUB = "-"
    MUL = "*"
    DIV = "/"
    MOD = "%"

    def _getPriority(self) -> int:
        match self:
            case MathOp.ADD | MathOp.SUB: return 0
            case MathOp.MOD             : return 1
            case MathOp.MUL | MathOp.DIV: return 2

    def hasPriorityOver(self, other:Self) -> bool:
        return self._getPriority() > other._getPriority()

    def exec[T](self, domain:SQLDomain, lhs:T, rhs:T) -> T:
        match self:
            case MathOp.ADD: return domain.add(lhs, rhs)
            case MathOp.SUB: return domain.sub(lhs, rhs)
            case MathOp.MUL: return domain.mul(lhs, rhs)
            case MathOp.DIV: return domain.div(lhs, rhs)
            case MathOp.MOD: return domain.mod(lhs, rhs)

type Literal = int|str|datetime
class MathExpr:
    def __init__(self, lhs:Attribute|Literal|Self, op:Optional[MathOp] = None, rhs:Optional[Attribute|Literal|Self] = None) -> None:
        self.lhs, self.op, self.rhs = lhs, op, rhs

    def addOperation(self, op:MathOp) -> tuple[Self, Self]:
        """
        Returns a tuple of 2 values:
        - The entire MathExpr tree up to this point always including the new operation, even when it's the new root.
        - The rightmost tail, where the next operations will be added.
        """
        if not self.op:
            self.op = op
            return self, self
        
        if op.hasPriorityOver(self.op):
            if isinstance(self.rhs, MathExpr): self.rhs, tail = self.rhs.addOperation(op)
            else: tail = self.rhs = MathExpr(self.rhs, op)
            return self, tail

        newRoot = MathExpr(self, op)
        return newRoot, newRoot # When the new operation is the new root it also contains the rightmost tail.

    def lastRightOperation(self) -> Self:
        return self.rhs.lastRightOperation() if isinstance(self.rhs, MathExpr) else self

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

    def exec[T](self, domain:SQLDomain, lhs:T, rhs:T) -> bool:
        match self:
            case CompareOp.EQUALS:                           return domain.compareEqs(lhs, rhs)
            case CompareOp.NOT_EQUALS | CompareOp.DIFFERENT: return domain.compareNeq(lhs, rhs)
            case CompareOp.GREATER_EQUALS:                   return domain.compareGre(lhs, rhs)
            case CompareOp.LESS_EQUALS:                      return domain.compareLse(lhs, rhs)
            case CompareOp.GREATER:                          return domain.compareGrt(lhs, rhs)
            case CompareOp.LESS:                             return domain.compareLst(lhs, rhs)

class Predicate[T]:
    def __init__(self, attr:Attribute, op:CompareOp, value:T) -> None:
        self.attr, self.op, self.value = attr, op, value
    
    def isSatisfied(self, domain:SQLDomain, attrValueInTable:T) -> bool:
        return self.op.exec(domain, attrValueInTable, self.value)

def main() -> None:
    # a + (((b * c) / d) % e) - (f % (g * h)) + i
    e = MathExpr(Attribute("a"), MathOp.ADD, Attribute("b"))
    
    e, t = e.addOperation(MathOp.MUL)
    t.rhs = Attribute("c")

    e, t = e.addOperation(MathOp.DIV)
    t.rhs = Attribute("d")

    e, t = e.addOperation(MathOp.MOD)
    t.rhs = Attribute("e")

    e, t = e.addOperation(MathOp.SUB)
    t.rhs = Attribute("f")

    e, t = e.addOperation(MathOp.MOD)
    t.rhs = Attribute("g")

    e, t = e.addOperation(MathOp.MUL)
    t.rhs = Attribute("h")

    e, t = e.addOperation(MathOp.ADD)
    t.rhs = Attribute("i")

    print(e)

if __name__ == "__main__": main()