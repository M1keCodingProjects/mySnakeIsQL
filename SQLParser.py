from Utils import *
from SQLTokenizer import *
from TableManager import Column, loadTable
from enum import Enum, StrEnum, auto

class SQLParser:
    class Keyword(Enum):
        SELECT = auto()
        FROM   = auto()

    class UnexpectedEOIErr(CustomErr):
        MSG = "Unexpected end of input"

    class TokenTypeErr(CustomErr):
        MSG = "Unexpected token"
        def __init__(self, expectedTokenType = Token.TokenType, actualToken = Token) -> None:
            super().__init__(f"Expected {expectedTokenType} but got {actualToken.type}({actualToken.value}) instead")

    def __init__(self) -> None:
        self.reset()
        self.tokenizer = SQLTokenizer([kw.name for kw in self.Keyword])
        
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
        if selectKw.value != "SELECT":
            return Res.Err(Exception(f"A query must begin with a SELECT clause, found \"{selectKw.value}\" instead"))

        # Attr
        if (firstSelectedColumn := self.parseAttribute()).isErr(): return firstSelectedColumn
        selectedColumns :list[Column.ColumnName] = [firstSelectedColumn.unwrap().value]

        # ("," Attr)*
        # Here it's not the SELECT clause's responsability to demand that something must exist after the first
        # attribute, the reason why I don't set mustExist = False here is that the token is not consumed: we
        # are just checking wether there's a comma there. If not (nothing = not a comma) we are done with SELECT.
        while self.getNextToken(Token.TokenType.COMMA, isConsumed = False).isOk():
            self.getNextToken() # Now if it is there we must consume it.
            if (selectedColumn := self.parseAttribute()).isErr(): return selectedColumn
            selectedColumns.append(selectedColumn.unwrap().value)

        return Res.Ok(selectedColumns)
    
    def parseFromClause(self) -> Res[str, Exception]:
        #TODO: avoid repetition: make a method to search for a specific keyword
        # "FROM"
        if (fromKw := self.getNextToken(Token.TokenType.KEYWORD)).isErr(): return fromKw
        fromKw = fromKw.unwrap()
        if fromKw.value != "FROM":
            return Res.Err(Exception(f"A query must contain a FROM clause, found \"{fromKw.value}\" instead"))
        
        # Table
        return self.parseTable().map(lambda token : token.value)

    def parseAttribute(self) -> Res[Token, UnexpectedEOIErr|TokenTypeErr]:
        # IDENT
        return self.getNextToken(Token.TokenType.IDENT)
    
    def parseTable(self) -> Res[Token, UnexpectedEOIErr|TokenTypeErr]:
        # IDENT
        return self.getNextToken(Token.TokenType.IDENT)

    def isStreamFinished(self) -> bool: return self.cursor >= len(self.tokens)
    
    #TODO: Someone really should implement Opt<T> in the Utils module...    
    def getNextToken(self, ofType :Token.TokenType|None = None, *, isConsumed = True, mustExist = True) -> Res[
        Token|None, UnexpectedEOIErr|TokenTypeErr]:

        try: token = self.tokens[self.cursor]
        except: return Res.Err(self.UnexpectedEOIErr()) if mustExist else Res.Ok(None)
        finally:
            if isConsumed: self.cursor += 1
        
        return Res.Ok(token) if not ofType or ofType == token.type else Res.Err(self.TokenTypeErr(ofType, token))

    def tokenize(self, programText:str) -> Res[None, Exception]:
        if (tokenizationRes := self.tokenizer.tokenize(programText)).isErr(): return tokenizationRes
        
        self.tokens = tokenizationRes.unwrap()
        return Res.Ok(None)