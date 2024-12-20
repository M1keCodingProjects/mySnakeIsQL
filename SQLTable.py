from Utils        import *
from typing       import *
from Predicate    import *
from SQLSchema    import Schema
from SQLTokenizer import Token

ENTITY_SEP_IS_DISPLAYED = False

class Table:
    MIN_COLUMN_WIDTH = 10
    def __init__(self, name:str, schema:Schema, instance :list = []) -> None:
        self.name, self.schema, self.instance = name, schema, instance

        self._columnsAmt = self.schema.getColumnsAmount()
        self._entriesAmt = len(instance) // self._columnsAmt
        self.setGraphics()

    def setGraphics(self):
        columnNames           = list(self.schema.getActualNames())
        self._columnNamesLens = list(map(lambda name : max(len(name), self.MIN_COLUMN_WIDTH), columnNames))
        actualColumnSizes     = list(map(lambda l : l + 2, self._columnNamesLens))
        
        schemaLine         = "".join([ f"│ {name.center(self.MIN_COLUMN_WIDTH)} " for name in columnNames ]) + "│\n"
        self.entrySepLine  = '├' + produceTableSepWithDivits(actualColumnSizes, '┼') + "┤\n"
        self.bottomLine    = '└' + produceTableSepWithDivits(actualColumnSizes, '┴') + "┘\n"
        self.schemaDisplay = '┌' + produceTableSepWithDivits(actualColumnSizes, '┬') + "┐\n" + schemaLine + self.entrySepLine * (not ENTITY_SEP_IS_DISPLAYED)

    def getCell(self, rowId:int, colId:int) -> Any:
        return self.instance[rowId * self._columnsAmt + colId]

    def getRow(self, rowId:int) -> list:
        entryStartPos = rowId * self._columnsAmt
        return self.instance[entryStartPos:entryStartPos + self._columnsAmt]

    def getColumn(self, colId:int) -> list:
        return self.instance[colId::self._columnsAmt]

    def select(self, columnNames:list[str]) -> Res[Self, Schema.ColumnNameErr|Schema.ColumnNameCollisionErr]:
        newSchema = Schema()
        selectedColumnsIds :list[int] = []
        for columnName in columnNames:
            if columnName == Token.TokenType.ALL.value:
                newSchema          = self.schema.copy()
                selectedColumnsIds = list(range(self._columnsAmt))
                break

            if (selectedColumn := self.schema.getIdAndDomain(columnName)).isErr(): return selectedColumn
            
            id, domain = selectedColumn.unwrap()
            newSchema.addColumn(domain)
            selectedColumnsIds.append(id)

        newInstance = []
        for rowId in range(self._entriesAmt):
            for columnId in selectedColumnsIds:
                newInstance.append(self.getCell(rowId, columnId))

        return Res.Ok(Table("", newSchema, newInstance))

    def join(self, table:Self, pred:Optional[Predicate]) -> Res[Self, Schema.ColumnNameCollisionErr]:
        """ Will perform the cartesian product if pred is None """
        schema = Schema.merge( #TODO: solve collisions
            self.schema.copy(),
            table.schema.copy())
        
        instance = []
        for rowIdL in range(self._entriesAmt):
            leftRow = self.getRow(rowIdL)
            for rowIdR in range(table._entriesAmt):
                instance.extend(leftRow + table.getRow(rowIdR))
        
        return Res.Ok(Table("", schema, instance))

    def where(self, pred:Predicate) -> Res[Self, Schema.ColumnNameErr|SQLDomain.DomainValueErr]:
        if (column := self.schema.getIdAndDomain(pred.attrName)).isErr(): return column

        colId, domain = column.unwrap()
        if not domain.canValidate(pred.value):
            return Res.Err(SQLDomain.DomainValueErr(domain, pred.value, f"invalid predicate comparing attribute \"{pred.attrName}\" of type {domain.TYPE} with value \"{pred.value}\" of type {type(pred.value)}"))

        newInstance = []
        for rowId in range(self._entriesAmt):
            if pred.isSatisfied(domain, self.getCell(rowId, colId)):
                newInstance.extend(self.getRow(rowId))

        return Res.Ok(Table("", self.schema.copy(), newInstance))

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
        return Table(self.name, self.schema.copy(), self.instance.copy())

def main() -> None:
    pass

if __name__ == '__main__': main()