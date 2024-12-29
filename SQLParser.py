from datetime     import datetime
from Utils        import CustomErr, formatIntoDetails
from typing       import *
from SQLQuery     import Query
from Predicate    import *
from SQLTokenizer import *

class SQLParser:
    class UnexpectedEOIErr(CustomErr):
        MSG = "Unexpected end of input"
        def __init__(self, expectedTokenType :Token.TokenType = None) -> None:
            super().__init__(f"expected {expectedTokenType if expectedTokenType else 'content'}")

    class TokenTypeErr(CustomErr):
        MSG = "Unexpected token"
        def __init__(self, expectedTokenType:Token.TokenType|list[Token.TokenType], actualToken:Token) -> None:
            super().__init__(f"expected {
                ' or '.join(expectedTokenType) if isinstance(expectedTokenType, list) else expectedTokenType
            } but got {actualToken.type}({actualToken.value}) instead")

    class KeywordErr(CustomErr):
        MSG = "Unexpected keyword in context"
        def __init__(self, expectedKeyword:SQLTokenizer.Keyword, actualKeyword:SQLTokenizer.Keyword, detailsMsg = "") -> None:
            super().__init__(f"expected {expectedKeyword.name} clause{
                formatIntoDetails(detailsMsg, "")} but got keyword \"{actualKeyword.name}\" instead")

    def __init__(self) -> None:
        self.reset()
        self.tokenizer = SQLTokenizer()
        
    def reset(self):
        self.cursor :int         = 0
        self.tokens :list[Token] = []
        self.parsedQuery         = Query()

    def parse(self, programText:str) -> Res[None, Exception]:
        print("Parsing query..")
        self.reset()

        if (tokenizationRes := self.tokenize(programText)).isErr(): return tokenizationRes
        
        # The first line must be a SELECT clause:
        if (selectedColumns := self.parseSelectClause()).isErr(): return selectedColumns
        self.parsedQuery.setColumnNames(*selectedColumns.unwrap())

        # The second line must be a FROM clause:
        if (tables := self.parseFromClause()).isErr(): return tables
        self.parsedQuery.setTableNames(*tables.unwrap())

        # The third line must be a WHERE clause or nothing:
        if (wherePred := self.parseWhereClause()).isErr(): return wherePred
        if wherePred  := wherePred.unwrap(): self.parsedQuery.setWherePredicate(wherePred)

        # There can be an optional ";" at the end:
        if (queryEnd := self.getNextToken(Token.TokenType.END, mustExist = False)).isErr(): return queryEnd

        # Then we must be done:
        if not self.isStreamFinished(): return Res.Err(Exception("Unexpected trailing content after end of query"))

        print("Query parsed successfully.")
        return Res.Ok(None)
    
    def parseSelectClause(self) -> Res[list[str], Exception]:
        # "SELECT"
        if (selectKw := self.getKeyword(SQLTokenizer.Keyword.SELECT, "at the start of query")).isErr():
            return selectKw

        # Attr
        if (firstSelectedColumn := self.parseAttribute()).isErr(): return firstSelectedColumn
        selectedColumns = [firstSelectedColumn.unwrap().name]
        #TODO: Here it might make sense to keep the whole attribute instances

        # ("," Attr)*
        # Here it's not the SELECT clause's responsability to demand that something must exist after the first
        # attribute, the reason why I don't set mustExist = False here is that the token is not consumed: we
        # are just checking wether there's a comma there. If not (nothing = not a comma) we are done with SELECT.
        while self.getNextToken(Token.TokenType.COMMA, isConsumed = False).isOk():
            if(selectedColumns[-1] == MathOp.MUL.value):
                return Res.Err(Exception("Cannot select all (*) and also other attributes."))

            self.advance() # Now if it is there we must consume it.
            if (selectedColumn := self.parseAttribute()).isErr(): return selectedColumn
            
            selectedColumns.append(selectedColumn.unwrap().name)

        return Res.Err(
            Exception("Cannot select all (*) and also other attributes."
        )) if len(selectedColumns) > 1 and (selectedColumns[-1] == MathOp.MUL.value) else Res.Ok(selectedColumns)
    
    def parseFromClause(self) -> Res[list[str], KeywordErr|UnexpectedEOIErr|TokenTypeErr]:
        # "FROM"
        if (fromKw := self.getKeyword(SQLTokenizer.Keyword.FROM, "after SELECT clause")).isErr():
            return fromKw
        
        # Table
        if (firstTable := self.parseTable()).isErr(): return firstTable
    
        #TODO: add method to parse comma-separated lists
        # ("," Table)*
        tables = [firstTable.unwrap().value]
        while self.getNextToken(Token.TokenType.COMMA, isConsumed = False).isOk():
            self.advance()
            if (table := self.parseTable()).isErr(): return table
            
            tables.append(table.unwrap().value)

        return Res.Ok(tables)

    def parseWhereClause(self) -> Res[Optional[Predicate], Exception]:
        # WHERE
        # Here if the next token is nothing or not a keyword it's no longer our responsibility:
        if (whereKw := self.getKeyword(SQLTokenizer.Keyword.WHERE, "after FROM clause", isOpt = True)).isErr():
            return whereKw if isinstance(whereKw.err, self.KeywordErr) else Res.Ok(None)

        # Predicate : Attr CompareOp Value
        # Attr
        if (attr := self.parseAttribute(canBeAll = False)).isErr(): return attr

        # CompareOp
        if (op := self.parseCompareOp()).isErr(): return op

        # Value
        if (value := self.parseValue()).isErr(): return value

        return Res.Ok(Predicate(attr.unwrap(), op.unwrap(), value.unwrap()))

    def parseMathExpr(self) -> Res[MathExpr, Exception]:
        # Operand | (MathExpr MathOp)* MathExpr
        # Operand
        if (firstOperand := self.parseOperand()).isErr(): return firstOperand

        # (MathExpr MathOp)* MathExpr
        mathExpr = MathExpr(firstOperand.unwrap())
        while (operator := self.parseMathOp(isConsumed = False)).isOk():
            mathExpr, tail = mathExpr.addOperation(operator.unwrap())
            self.advance()

            if (operand := self.parseOperand()).isErr(): return operand
            tail.rhs = operand.unwrap()
        
        return Res.Ok(mathExpr)
        
    def parseOperand(self) -> Res[Literal|Attribute, Exception]:
        # Literal | Attr :
        operand = self.parseAttribute(canBeAll = False, isConsumed = False)
        if operand.isErr() and (operand := self.parseValue()).isErr(): return operand

        operand = operand.unwrap()
        if isinstance(operand, Attribute): self.advance()
        return Res.Ok(operand)

    def parseValue(self) -> Res[Literal, UnexpectedEOIErr|TokenTypeErr|ValueError]:
        if (token := self.getNextToken([Token.TokenType.INT, Token.TokenType.STR, Token.TokenType.DATE])).isErr():
            return token
        
        # God I hate python.. anyways, "value" should never be Unbound here.
        match (token := token.unwrap()).type:
            case Token.TokenType.INT:  value = int(token.value)
            case Token.TokenType.STR:  value = token.value[1:-1]  # vvv we flip because constructor wants y, m, d
            case Token.TokenType.DATE:
                if (date := Res.wrap(datetime, *map(int, token.value.split('\\')[::-1]))).isErr(): return date
                value     = date.unwrap()
            
            case _: raise Exception("Should never happen")
        
        return Res.Ok(value)
    
    def parseMathOp(self, *, isConsumed = True) -> Res[MathOp, UnexpectedEOIErr|TokenTypeErr]:
        # "+" | "-" | "*" | "/" | "%"
        return self.getNextToken(Token.TokenType.MATH_OP, isConsumed = isConsumed).map(lambda token : MathOp(token.value))

    def parseCompareOp(self) -> Res[CompareOp, UnexpectedEOIErr|TokenTypeErr]:
        # "==" | "!=" | "<>" | "<" | ">" | ">=" | "<="
        return self.getNextToken(Token.TokenType.COMPARE_OP).map(lambda token : CompareOp(token.value))

    def parseAttribute(self, *, canBeAll = True, isConsumed = True) -> Res[Attribute, Exception]:
        # "*" | IDENT
        acceptedTokenTypes = [Token.TokenType.IDENT]
        if canBeAll: acceptedTokenTypes.append(Token.TokenType.MATH_OP)
        # Error reporting is a bit wonky here ^^^, this is gonna change soon anyways so I'm not too preoccupied.
        if (attr := self.getNextToken(acceptedTokenTypes, isConsumed = isConsumed)).isErr(): return attr

        attr = attr.unwrap()
        if attr.type == Token.TokenType.MATH_OP and attr.value != MathOp.MUL.value:
            return Res.Err(self.TokenTypeErr(acceptedTokenTypes[0]))
        
        return Res.Ok(Attribute(attr.value))
    
    def parseTable(self) -> Res[Token, UnexpectedEOIErr|TokenTypeErr]:
        # IDENT
        return self.getNextToken(Token.TokenType.IDENT)

    def getKeyword(self, expKeyword:SQLTokenizer.Keyword, detailsErrMsg = "", *, isOpt = False) -> Res[None, KeywordErr|UnexpectedEOIErr|TokenTypeErr]:
        if (keyword := self.getNextToken(Token.TokenType.KEYWORD, isConsumed = not isOpt)).isErr(): return keyword
        
        if isOpt: self.advance()
        keyword = SQLTokenizer.Keyword(keyword.unwrap().value.upper())
        return Res.Ok(None) if keyword == expKeyword else Res.Err(self.KeywordErr(expKeyword, keyword, detailsErrMsg))

    def isStreamFinished(self) -> bool: return self.cursor >= len(self.tokens)
    
    def advance(self, amount = 1) -> None:
        self.cursor += amount

    #TODO: Someone really should implement Opt<T> in the Utils module...    
    def getNextToken(self, ofType :Token.TokenType|list[Token.TokenType] = None, *, isConsumed = True, mustExist = True) -> Res[Token|None, UnexpectedEOIErr|TokenTypeErr]:
        try: token = self.tokens[self.cursor]
        except: return Res.Err(self.UnexpectedEOIErr(ofType)) if mustExist else Res.Ok(None)
        finally:
            if isConsumed: self.advance()
        
        match ofType:
            case None:             return Res.Ok(token)
            case [*acceptedTypes]: return Res.Ok(token) if token.type in acceptedTypes else Res.Err(self.TokenTypeErr(ofType, token))
            case acceptedType:     return Res.Ok(token) if token.type == acceptedType  else Res.Err(self.TokenTypeErr(ofType, token))

    def tokenize(self, programText:str) -> Res[None, Exception]:
        if (tokenizationRes := self.tokenizer.tokenize(programText)).isErr(): return tokenizationRes
        
        self.tokens = tokenizationRes.unwrap()
        return Res.Ok(None)

def main() -> None:
    p = SQLParser()
    p.reset()
    p.tokenize("a + b * \"Bob\" / d % 12 - f % g * 12\\03\\2002 + i")
    print(p.tokens)

    print(p.parseMathExpr().unwrap())

if __name__ == "__main__": main()