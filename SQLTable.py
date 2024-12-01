from Utils        import *
from typing       import *
from Predicate    import *
from SQLDomain    import *
from SQLTokenizer import Token

ENTITY_SEP_IS_DISPLAYED = False

class Schema:
    class ColumnNameCollisionErr(CustomErr):
        MSG = "Column name collision"
        def __init__(self, columnName:str) -> None:
            super().__init__(f"a column called \"{columnName}\" is already present in the schema")

    class ColumnNameErr(CustomErr):
        MSG = "Unknown column"
        def __init__(self, columnName:str) -> None:
            super().__init__(f"a column called \"{columnName}\" is not present in the schema")

    def __init__(self) -> None:
        self.__columns :dict[str, tuple[int, SQLDomain]] = {}

    def getColumnsAmount(self) -> int:
        return len(self.__columns)

    def addColumn(self, columnName:str, domain:SQLDomain) -> Res[None, "Schema.ColumnNameCollisionErr"]:
        columnName = columnName.upper()
        if columnName in self.__columns: return Res.Err(Schema.ColumnNameCollisionErr(columnName))

        self.__columns[columnName] = (self.getColumnsAmount(), domain)
        return Res.Ok()

    def iterNames(self) -> KeysView[str]:
        return self.__columns.keys()

    def iterIdsAndDomains(self) -> ValuesView[tuple[int, SQLDomain]]:
        return self.__columns.values()

    def iterColumns(self) -> ItemsView[str, tuple[int, SQLDomain]]:
        return self.__columns.items()

    def getIdAndDomain(self, name:str) -> Res[tuple[int, SQLDomain], "Schema.ColumnNameErr"]:
        return Res.wrap(lambda name : self.__columns[name], name).mapErr(lambda _ : Schema.ColumnNameErr(name))
        #^^^ here I could grab the name simply by passing the KeyError along directly but it looks too criptic imo.

    def __repr__(self) -> str:
        return "\n".join([f"Column #{cId} \"{name}\" : {domain}" for name, (cId, domain) in self.__columns.items()])

    def copy(self) -> Self:
        newInst = Schema()
        newInst.__columns = { name : (cId, domain.copy()) for name, (cId, domain) in self.__columns.items() }
        return newInst

class Table:
    MIN_COLUMN_WIDTH = 10
    def __init__(self, schema:Schema, instance :list = []) -> None:
        self.schema, self.instance = schema, instance

        self._columnsAmt = self.schema.getColumnsAmount()
        self._entriesAmt = len(instance) // self._columnsAmt
        self.setGraphics()

    def setGraphics(self):
        columnNames           = self.schema.iterNames()
        self._columnNamesLens = list(map(lambda name : max(len(name), self.MIN_COLUMN_WIDTH), columnNames))
        actualColumnSizes     = list(map(lambda l : l + 2, self._columnNamesLens))
        
        schemaLine         = "".join([ f"│ {name.center(self.MIN_COLUMN_WIDTH)} " for name in columnNames ]) + "│\n"
        self.entrySepLine  = '├' + produceTableSepWithDivits(actualColumnSizes, '┼') + "┤\n"
        self.bottomLine    = '└' + produceTableSepWithDivits(actualColumnSizes, '┴') + "┘\n"
        self.schemaDisplay = '┌' + produceTableSepWithDivits(actualColumnSizes, '┬') + "┐\n" + schemaLine + self.entrySepLine * (not ENTITY_SEP_IS_DISPLAYED)

    def select(self, columnNames:list[str]) -> Res[Self, Schema.ColumnNameErr|Schema.ColumnNameCollisionErr]:
        newSchema = Schema()
        selectedColumnsIds :list[int] = []
        for columnName in columnNames:
            if columnName == Token.TokenType.ALL.value:
                newSchema          = self.schema.copy()
                selectedColumnsIds = list(range(self._columnsAmt)); break

            if (selectedColumn := self.schema.getIdAndDomain(columnName)).isErr(): return selectedColumn
            
            id, domain = selectedColumn.unwrap()
            if (collisionRes := newSchema.addColumn(columnName, domain)).isErr(): return collisionRes

            selectedColumnsIds.append(id)

        newInstance = []
        for rowId in range(self._entriesAmt):
            cellY = rowId * self._columnsAmt
            for columnId in selectedColumnsIds:
                newInstance.append(self.instance[columnId + cellY])

        return Res.Ok(Table(newSchema, newInstance))

    def where(self, pred:Predicate) -> Res[Self, Schema.ColumnNameErr|SQLDomain.DomainValueErr]:
        if (column := self.schema.getIdAndDomain(pred.attrName)).isErr(): return column

        id, domain = column.unwrap()
        if not domain.canValidate(pred.value):
            return Res.Err(SQLDomain.DomainValueErr(domain, pred.value, f"invalid predicate comparing attribute \"{pred.attrName}\" of type {domain} with value \"{pred.value}\" of type {type(pred.value)}"))

        newInstance = []
        for rowId in range(self._entriesAmt):
            cellY = rowId * self._columnsAmt
            if pred.isSatisfied(self.instance[id + cellY]):
                newInstance.extend(self.instance[cellY:cellY + self._columnsAmt])

        return Res.Ok(Table(self.schema.copy(), newInstance))

    def __repr__(self) -> str:
        tableStr = self.schemaDisplay
        for y in range(self._entriesAmt):
            tableStr += self.entrySepLine * ENTITY_SEP_IS_DISPLAYED
            for x in range(self._columnsAmt):
                strValue      = str(self.instance[x + y * self._columnsAmt])
                columnNameLen = self._columnNamesLens[x]

                if len(strValue) > columnNameLen: strValue = strValue[:columnNameLen - 3] + "..."
                tableStr += f"│ {strValue.center(columnNameLen)} "

            tableStr += "│\n"

        return tableStr + self.bottomLine
    
    def copy(self) -> str:
        return Table(self.schema.copy(), self.instance.copy())

def main() -> None:
    pass

if __name__ == '__main__': main()