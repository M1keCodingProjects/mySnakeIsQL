import re
from enum      import StrEnum
from Utils     import Res, asPatternOpts
from Predicate import LogicOp, CompareOp, MathOp

class Token:
    class TokenType(StrEnum):
        UNKNOWN    = "unknown"
        IGNORED    = "ignored"
        KEYWORD    = "keyword"
        LPAREN     = "("
        RPAREN     = ")"
        COMMA      = ","
        END        = ";"
        LOGIC_OP   = "logical operator"
        COMPARE_OP = "comparison operator"
        INT        = "integer"
        MATH_OP    = "math operator"
        STR        = "string"
        DATE       = "date"
        IDENT      = "identifier"

        def __repr__(self) -> str:
            return f"\"{self.value}\""
    
    def __init__(self, type:TokenType, value:str) -> None:
        self.type, self.value = type, value

    def __repr__(self) -> str: return f"{self.type}({self.value})"

class SQLTokenizer:
    class Keyword(StrEnum):
        SELECT = "SELECT"
        FROM   = "FROM"
        WHERE  = "WHERE"
    
    def __init__(self) -> None:
        keywords   = [kw.name  for kw in SQLTokenizer.Keyword]
        logicOps   = [op.value for op in LogicOp]
        compareOps = [op.value for op in CompareOp]
        mathOps    = ['\\' + op.value for op in MathOp]

        self.rules = tuple(map(lambda rule : (re.compile('^' + rule[0], re.IGNORECASE), rule[1]), (
            (r"\s+",                    Token.TokenType.IGNORED),
            (r",",                      Token.TokenType.COMMA),
            (r";",                      Token.TokenType.END),
            (r"\(",                     Token.TokenType.LPAREN),
            (r"\)",                     Token.TokenType.RPAREN),
            (r"\d\d?\\\d\d?\\\d{4}",    Token.TokenType.DATE),
            (r"-?\d+",                  Token.TokenType.INT),
            (asPatternOpts(mathOps),    Token.TokenType.MATH_OP),
            (r"(\"|\').*?\1",           Token.TokenType.STR),
            (asPatternOpts(compareOps), Token.TokenType.COMPARE_OP),
            (asPatternOpts(logicOps),   Token.TokenType.LOGIC_OP),
            (asPatternOpts(keywords),   Token.TokenType.KEYWORD),
            (r"[a-zA-Z_]\w*",           Token.TokenType.IDENT),
        )))

    def tokenize(self, text:str) -> Res[list[Token], Exception]:
        tokens :list[Token] = []

        cursor   = 0
        textSize = len(text)
        while cursor < textSize:
            textToVisit = text[cursor:]
            for rule, tokenType in self.rules:
                if not (m := re.match(rule, textToVisit)): continue

                tokenValue = m.group()
                if tokenType != Token.TokenType.IGNORED: tokens.append(Token(tokenType, tokenValue))
                cursor += len(tokenValue)
                break
            
            # when no rule is satisfied
            else: return Res.Err(Exception(f"Encountered unrecognized token at \"{textToVisit[:30]}...\""))

        return Res.Ok(tokens)