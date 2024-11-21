from Utils import *
from Predicate import *
from SQLTokenizer import *
from TableManager import Column, loadTable
from enum import Enum, StrEnum, auto

class SQLParser:
    class Keyword(Enum):
        SELECT = auto()
        FROM   = auto()
        WHERE  = auto()

    class UnexpectedEOIErr(CustomErr):
        MSG = "Unexpected end of input"
        def __init__(self, expectedTokenType :Token.TokenType = None) -> None:
            super().__init__(f"Expected {expectedTokenType if expectedTokenType else 'content'}")

    class TokenTypeErr(CustomErr):
        MSG = "Unexpected token"
        def __init__(self, expectedTokenType:Token.TokenType|list[Token.TokenType], actualToken:Token) -> None:
            super().__init__(f"Expected {
                ' or '.join(expectedTokenType) if isinstance(expectedTokenType, list) else expectedTokenType
            } but got {actualToken.type}({actualToken.value}) instead")

    def __init__(self) -> None:
        self.reset()
        self.tokenizer = SQLTokenizer(self.Keyword)
        
    def reset(self):
        self.cursor :int         = 0
        self.tokens :List[Token] = []
        self.parsedQuery         = {}

    def parse(self, programText:str) -> Res[None, Exception]:
        print("Parsing query..")
        self.reset()

        if (tokenizationRes := self.tokenize(programText)).isErr(): return tokenizationRes
        
        #TODO: possibly a decent intermediate representation for parsing..

        # The first line must be a SELECT clause:
        if (selectedColumns := self.parseSelectClause()).isErr(): return selectedColumns
        self.parsedQuery["selectedColumns"] = selectedColumns.unwrap()

        # The second line must be a FROM clause:
        if (table := self.parseFromClause()).isErr(): return table
        self.parsedQuery["table"] = table.unwrap()

        # The third line must be a WHERE clause or nothing:
        if (wherePred := self.parseWhereClause()).isErr(): return wherePred
        self.parsedQuery["where"] = wherePred.unwrap()

        # There can be an optional ";" at the end:
        if (queryEnd := self.getNextToken(Token.TokenType.END, mustExist = False)).isErr(): return queryEnd

        # Then we must be done:
        if not self.isStreamFinished(): return Res.Err(Exception("Unexpected trailing content after end of query"))

        print("Query parsed successfully.")
        return Res.Ok(None)
    
    def parseSelectClause(self) -> Res[list[Column.ColumnName], Exception]:
        # "SELECT"
        if (selectKw := self.getNextToken(Token.TokenType.KEYWORD)).isErr(): return selectKw
        selectKw = selectKw.unwrap()
        if selectKw.value != self.Keyword.SELECT.name:
            return Res.Err(Exception(f"A query must begin with a {self.Keyword.SELECT.name} clause, found \"{selectKw.value}\" instead"))

        # Attr
        if (firstSelectedColumn := self.parseAttribute()).isErr(): return firstSelectedColumn
        selectedColumns :list[Column.ColumnName] = [firstSelectedColumn.unwrap().value]

        # ("," Attr)*
        # Here it's not the SELECT clause's responsability to demand that something must exist after the first
        # attribute, the reason why I don't set mustExist = False here is that the token is not consumed: we
        # are just checking wether there's a comma there. If not (nothing = not a comma) we are done with SELECT.
        while self.getNextToken(Token.TokenType.COMMA, isConsumed = False).isOk():
            if(selectedColumns[-1] == Token.TokenType.ALL.value):
                return Res.Err(Exception("Cannot select all (*) and also other attributes."))

            self.getNextToken() # Now if it is there we must consume it.
            if (selectedColumn := self.parseAttribute()).isErr(): return selectedColumn
            
            selectedColumns.append(selectedColumn.unwrap().value)

        return Res.Err(
            Exception("Cannot select all (*) and also other attributes."
        )) if len(selectedColumns) > 1 and (selectedColumns[-1] == Token.TokenType.ALL) else Res.Ok(selectedColumns)
    
    def parseFromClause(self) -> Res[str, Exception]:
        #TODO: avoid repetition: make a method to search for a specific keyword
        # "FROM"
        if (fromKw := self.getNextToken(Token.TokenType.KEYWORD)).isErr(): return fromKw
        fromKw = fromKw.unwrap()
        if fromKw.value != self.Keyword.FROM.name:
            return Res.Err(Exception(f"A query must contain a {self.Keyword.FROM.name} clause, found \"{fromKw.value}\" instead"))
        
        # Table
        return self.parseTable().map(lambda token : token.value)

    def parseWhereClause(self) -> Res[Optional[Predicate], Exception]:
        # WHERE
        # Here if the next token is nothing or not a keyword it's no longer our responsibility:
        if (whereKw := self.getNextToken(Token.TokenType.KEYWORD, isConsumed = False)).isErr(): return Res.Ok(None)
        
        self.cursor += 1
        whereKw = whereKw.unwrap()
        if whereKw.value != self.Keyword.WHERE.name:
            return Res.Err(Exception(f"A query must contain a {self.Keyword.WHERE.name} clause after the {self.Keyword.FROM.name} clause, found \"{whereKw.value}\" instead"))

        # Predicate : Attr CompareOp Value
        # Attr
        if (attr := self.parseAttribute(canBeAll = False)).isErr(): return attr

        # CompareOp
        if (op := self.parseCompareOp()).isErr(): return op

        # Value
        if (value := self.parseValue()).isErr(): return value

        return Res.Ok(Predicate(attr.unwrap().value, op.unwrap(), value.unwrap()))

    def parseValue(self) -> Res[int|str, UnexpectedEOIErr|TokenTypeErr]:
        return self.getNextToken([Token.TokenType.INT, Token.TokenType.STR]).map(
            lambda token : int(token.value) if token.type == Token.TokenType.INT else token.value[1:-1])
    
    def parseCompareOp(self) -> Res[CompareOp, UnexpectedEOIErr|TokenTypeErr]:
        # "==" | "!=" | "<>" | "<" | ">" | ">=" | "<="
        return self.getNextToken(Token.TokenType.COMPARE_OP).map(lambda token : CompareOp(token.value))

    def parseAttribute(self, *, canBeAll = True) -> Res[Token, UnexpectedEOIErr|TokenTypeErr]:
        # "*" | IDENT
        acceptedTokenTypes = [Token.TokenType.IDENT]
        if canBeAll: acceptedTokenTypes.append(Token.TokenType.ALL)
        return self.getNextToken(acceptedTokenTypes)
    
    def parseTable(self) -> Res[Token, UnexpectedEOIErr|TokenTypeErr]:
        # IDENT
        return self.getNextToken(Token.TokenType.IDENT)

    def isStreamFinished(self) -> bool: return self.cursor >= len(self.tokens)
    
    #TODO: Someone really should implement Opt<T> in the Utils module...    
    def getNextToken(self, ofType :Token.TokenType|list[Token.TokenType] = None, *, isConsumed = True, mustExist = True) -> Res[Token|None, UnexpectedEOIErr|TokenTypeErr]:
        try: token = self.tokens[self.cursor]
        except: return Res.Err(self.UnexpectedEOIErr(ofType)) if mustExist else Res.Ok(None)
        finally:
            if isConsumed: self.cursor += 1
        
        match ofType:
            case None:             return Res.Ok(token)
            case [*acceptedTypes]: return Res.Ok(token) if token.type in acceptedTypes else Res.Err(self.TokenTypeErr(ofType, token))
            case acceptedType:     return Res.Ok(token) if token.type == acceptedType  else Res.Err(self.TokenTypeErr(ofType, token))

    def tokenize(self, programText:str) -> Res[None, Exception]:
        if (tokenizationRes := self.tokenizer.tokenize(programText)).isErr(): return tokenizationRes
        
        self.tokens = tokenizationRes.unwrap()
        return Res.Ok(None)