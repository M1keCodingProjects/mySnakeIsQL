from Utils     import Res
from typing    import *
from SQLTable  import Table, Schema
from SQLDomain import SQLDomain
from Predicate import Predicate

class Query:
    def __init__(self) -> None:
        self.tableName :str = ""
        self.wherePred :Optional[Predicate] = None
        self.selectedColumnNames :list[str] = []
    
    def setSelectedColumnNames(self, *columnNames:str) -> None:
        self.selectedColumnNames = list(columnNames)
    
    def setTableName(self, tableName:str) -> None:
        self.tableName = tableName
    
    def setWherePredicate(self, predicate:Predicate) -> None:
        self.wherePred = predicate
    
    def run(self, loadedTables:dict[str, Table]) -> Res[Table, Exception]:
        return Res.Ok(loadedTables
        ).flatMap(self._runFromClause
        ).flatMap(self._runWhereClause
        ).flatMap(self._runSelectClause)

    def _runFromClause(self, loadedTables:dict[str, Table]) -> Res[Table, KeyError]:
        return Res.wrap(lambda tableName : loadedTables[tableName], self.tableName)

    def _runSelectClause(self, table:Table) -> Res[Table, Schema.ColumnNameErr|Schema.ColumnNameCollisionErr]:
        return table.select(self.selectedColumnNames)

    def _runWhereClause(self, table:Table) -> Res[Table, Schema.ColumnNameErr|SQLDomain.DomainValueErr]:
        return table.where(self.wherePred) if self.wherePred else Res.Ok(table)