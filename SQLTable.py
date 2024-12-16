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

    def merge(left:Self, right:Self, *, duplicatesAreIgnored = False) -> Res[Self, "Schema.ColumnNameCollisionErr"]:
        """Static"""
        mergedSchema = left.copy()
        for _, domain in right.iterIdsAndDomains():
            if (res := mergedSchema.addColumn(domain)).isErr() and not duplicatesAreIgnored: return res
        
        return Res.Ok(mergedSchema)

    def getColumnsAmount(self) -> int:
        return len(self.__columns)

    def renameColumn(self, oldName:str, newName:str) -> Res[None, "Schema.ColumnNameCollisionErr|Schema.ColumnNameErr"]:
        """Mutates self, expects correct (lower) case."""
        if newName == oldName:            return Res.Ok(None)
        if newName     in self.__columns: return Res.Err(Schema.ColumnNameCollisionErr(newName))
        if oldName not in self.__columns: return Res.Err(Schema.ColumnNameErr(oldName))

        self.__columns[newName] = self.__columns.pop(oldName)
        return Res.Ok(None)

    def addColumn(self, domain:SQLDomain) -> Res[None, "Schema.ColumnNameCollisionErr"]:
        columnName = domain.name.lower()
        if columnName in self.__columns: return Res.Err(Schema.ColumnNameCollisionErr(domain.name))

        self.__columns[columnName] = (self.getColumnsAmount(), domain)
        return Res.Ok()

    def iterNames(self) -> KeysView[str]:
        return self.__columns.keys()

    def iterIdsAndDomains(self) -> ValuesView[tuple[int, SQLDomain]]:
        return self.__columns.values()

    def iterColumns(self) -> ItemsView[str, tuple[int, SQLDomain]]:
        return self.__columns.items()

    def getExactNames(self) -> list[str]:
        return list(map(lambda IdAndDomain : IdAndDomain[1].name, self.__columns.values()))

    def getIdAndDomain(self, name:str) -> Res[tuple[int, SQLDomain], "Schema.ColumnNameErr"]:
        return Res.wrap(lambda name : self.__columns[name], name.lower()).mapErr(lambda _ : Schema.ColumnNameErr(name))
        #^^^ here I could grab the name simply by passing the KeyError along directly but it looks too criptic imo.

    def __repr__(self) -> str:
        return "\n".join([f"Column #{cId} \"{name}\" : {domain}" for name, (cId, domain) in self.__columns.items()])

    def copy(self) -> Self:
        newInst = Schema()
        newInst.__columns = { name : (cId, domain.copy()) for name, (cId, domain) in self.__columns.items() }
        return newInst

class Table:
    MIN_COLUMN_WIDTH = 10
    def __init__(self, name:str, schema:Schema, instance :list = []) -> None:
        self.name, self.schema, self.instance = name, schema, instance

        self._columnsAmt = self.schema.getColumnsAmount()
        self._entriesAmt = len(instance) // self._columnsAmt
        self.setGraphics()

    def setGraphics(self):
        columnNames           = self.schema.getExactNames()
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
                selectedColumnsIds = list(range(self._columnsAmt)); break

            if (selectedColumn := self.schema.getIdAndDomain(columnName)).isErr(): return selectedColumn
            
            id, domain = selectedColumn.unwrap()
            if (collisionRes := newSchema.addColumn(domain)).isErr(): return collisionRes

            selectedColumnsIds.append(id)

        newInstance = []
        for rowId in range(self._entriesAmt):
            for columnId in selectedColumnsIds:
                newInstance.append(self.getCell(rowId, columnId))

        return Res.Ok(Table("", newSchema, newInstance))

    def join(self, table:Self, pred:Optional[Predicate]) -> Res[Self, Schema.ColumnNameCollisionErr]:
        """ Will perform the cartesian product if pred is None """
        if (schema := Schema.merge( #TODO: solve collisions
            self.schema.copy(),
            table.schema.copy())).isErr(): return schema
        
        instance = []
        for rowIdL in range(self._entriesAmt):
            leftRow = self.getRow(rowIdL)
            for rowIdR in range(table._entriesAmt):
                instance.extend(leftRow + table.getRow(rowIdR))
        
        return Res.Ok(Table("", schema.unwrap(), instance))

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
    schema = Schema()
    schema.addColumn(IntegerDomain("SId"))
    schema.addColumn(StringDomain("Name", 40))

    students = Table("Student", schema, [
        0, "John Doe",
        1, "Alice Bob",
    ])

    schema = Schema()
    schema.addColumn(IntegerDomain("CId"))
    schema.addColumn(StringDomain("CName", 40))

    courses = Table("Course", schema, [
        0, "Course 1",
        1, "Course 2",
        2, "Course 3",
    ])

    print(students.join(courses, None).unwrap())

if __name__ == '__main__': main()