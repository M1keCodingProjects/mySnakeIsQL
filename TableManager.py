from Utils    import *
from typing   import *
from datetime import *
from SQLTokenizer import Token
## Manage Data Source
class SubfolderAccessErr(CustomErr, OSError):
    MSG = "Table access paths must always be plain file names and cannot contain the \"/\" character"
    def __init__(self, path:str):
        super().__init__(f"Provided path:\"{path}\"")

def retrieveRawTableFromLoc(filename:str) -> Res[str, OSError]:
    # Prevent subfolder access:
    if '/' in filename: return Res.Err(SubfolderAccessErr(filename))

    with open(f"./Tables/{filename}.csv") as fd: return Res.wrap(fd.read)

## Decode Domains
class SQLDomain[T]:
    NAME = "default"
    def __init__(self) -> None:
        raise Exception("Cannot instantiate an instance of base: SQLDomain.")

    def canValidate(self, value:T) -> bool:
        raise Exception("Cannot call canValidate on an instance of base: SQLDomain.")

    def parseValue(self, valueStr:str) -> Res[T, Exception]:
        raise Exception("Cannot call parseValue on an instance of base: SQLDomain.")
    
    def __repr__(self) -> str:
        return self.NAME

class DomainSyntaxErr(CustomErr):
        MSG = "Couldn't parse string as valid domain"

class IntegerDomain(SQLDomain[int]):
    NAME = "integer"
    def __init__(self) -> None: pass
    def canValidate(self, value:int) -> bool:
        return isinstance(value, int)

    def parseValue(self, valueStr:str) -> Res[int, Exception]:
        return Res[int, ValueError].wrap(int, valueStr)

class StringDomain(SQLDomain[str]):
    NAME = "varchar"
    def __init__(self, maxLen:int) -> None:
        self.maxLen = maxLen
    
    def canValidate(self, value:str) -> bool:
        return isinstance(value, str) and len(value) < self.maxLen
    
    def parseValue(self, valueStr:str) -> Res[str, Exception]:
        return Res.Ok(valueStr)
    
    def __repr__(self) -> str:
        return super().__repr__() + f"({self.maxLen})"

class DateDomain(SQLDomain[datetime]):
    NAME = "date"
    def __init__(self) -> None: pass
    def canValidate(self, value:datetime) -> bool:
        return isinstance(value, datetime)

    def parseValue(self, valueStr:str) -> Res[datetime, Exception]:
        return Res[datetime, ValueError].wrap(datetime.strptime, valueStr, "%d/%m/%Y")

def parseDomain(domainStr:str) -> Res[SQLDomain, DomainSyntaxErr]:
    # TODO: rework with a builder or an automatic class.NAME -> class mapping because this introduces
    # heavy needless repetition and shaky responsibilities.
    if domainStr == IntegerDomain.NAME: return Res.Ok(IntegerDomain())
    if domainStr == DateDomain.NAME:    return Res.Ok(DateDomain())

    if (lparenPos := domainStr.find('(')) != -1:
        if domainStr[-1] != ')': return Res.Err(DomainSyntaxErr(f"Unclosed parentheses in \"{domainStr}\""))

        domainKw = domainStr[:lparenPos]
        if domainKw == StringDomain.NAME:
            return Res[int, ValueError
            ].wrap(int, domainStr[lparenPos + 1:-1] # maxLen portion gets passed to StringDomain
            ).map(lambda ml : StringDomain(ml)) # only if valid int

    return Res.Err(DomainSyntaxErr(f"Cannot recognize \"{domainStr}\" as any valid domain"))

class Column:
    type ColumnName = str
    def __init__(self, id:int, name:ColumnName, domain:SQLDomain) -> None:
        self.id, self.name, self.domain = id, name, domain

    def copy(self) -> Self: return Column(self.id, self.name, self.domain)

class Table:
    MIN_COLUMN_WIDTH = 10
    def __init__(self, schema:list[Column], instance :list = []) -> None:
        self.schema   = { column.name.upper() : column for column in schema }
        self.instance = instance

        self._entriesAmt      = len(instance)
        self._columnsAmt      = len(schema)
        self._columnNamesLens = list(map(
            lambda columnName : max(len(columnName), self.MIN_COLUMN_WIDTH), self.schema.keys()))

    def addRow(self, cells:list[str]) -> Res[None, Exception]:
        # This method directly operates on unparsed data, I don't think this is wise
        if len(cells) != self._columnsAmt: return Res.Err(Exception(
            f"Row length does not match table schema, expected {self._columnsAmt} cells but got {len(cells)}"))
        
        for valueStr, column in zip(cells, self.schema.values()):
            if (value := column.domain.parseValue(valueStr)).isErr(): return value
            self.instance.append(value.unwrap())
        
        self._entriesAmt += 1
        return Res.Ok(None)
    
    def select(self, columnNames:list[Column.ColumnName]) -> Res[Self, Exception]:
        """ It is assumed that all columnNames are fully capitalized. """
        newSchema          :list[Column] = []
        selectedColumnsPos :list[int]    = []
        for columnName in columnNames:
            if columnName == Token.TokenType.ALL.value:
                selectedColumnsPos = list(range(self._columnsAmt))
                newSchema = [column.copy() for column in self.schema.values()]
                break

            if (selectedColumn := Res[Column, KeyError].wrap(
                lambda columnName : self.schema[columnName], columnName)).isErr(): return selectedColumn
            
            selectedColumn :Column = selectedColumn.unwrap()
            selectedColumnsPos.append(selectedColumn.id)
            newSchema.append(selectedColumn)

        newInstance = []
        for rowId in range(self._entriesAmt):
            cellY = rowId * self._columnsAmt
            for columnId in selectedColumnsPos:
                newInstance.append(self.instance[columnId + cellY])

        return Res.Ok(Table(newSchema, newInstance))

    def __repr__(self) -> str:
        tableStr = "".join([
            f"| {column.name.center(self.MIN_COLUMN_WIDTH)} " for column in self.schema.values() ]) + "|\n"
        
        tableStr += '-' * (len(tableStr) - 1) + '\n'

        i = 0
        for cell in self.instance:
            strValue      = str(cell)
            columnNameLen = self._columnNamesLens[i]

            if len(strValue) > columnNameLen: strValue = strValue[:columnNameLen - 3] + "..."
            tableStr += f"| {strValue.center(columnNameLen)} "

            i = (i + 1) % self._columnsAmt
            if not i: tableStr += "|\n"

        return tableStr

#TODO: add a check somewhere to verify that table column names are all unique.

def loadTable(name:str) -> Res[Table, Exception]:
    if (tableRows := retrieveRawTableFromLoc(name)).isErr(): return tableRows
    tableRows = tableRows.unwrap().split('\n')

    columnNames  = tableRows[0].split(",")
    typeMetadata = tableRows[1].split(",")
    if len(columnNames) != len(typeMetadata): return Res.Err(Exception("Invalid schema"))

    i = 0
    columns :list[Column] = []
    for columnName, domainStr in zip(columnNames, typeMetadata):
        if (domain := parseDomain(domainStr)).isErr(): return domain
        columns.append(Column(i, columnName, domain.unwrap()))
        i += 1
    
    table = Table(columns)
    for entry in tableRows[2:]:
        if (res := table.addRow(entry.split(','))).isErr(): return res

    return Res.Ok(table)

def main() -> None:
    pass

if __name__ == '__main__': main()