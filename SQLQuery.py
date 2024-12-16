from Utils        import Res
from typing       import *
from SQLTable     import Table, Schema
from SQLDomain    import SQLDomain
from Predicate    import Predicate
from TableManager import TableManager

class Query:
    def __init__(self) -> None:
        self.wherePred   :Optional[Predicate] = None
        self.tableNames  :list[str] = []
        self.columnNames :list[str] = []
    
    def setColumnNames(self, *columnNames:str) -> None:
        self.columnNames = list(columnNames)
    
    def setTableNames(self, *tableNames:str) -> None:
        self.tableNames = list(tableNames)
    
    def setWherePredicate(self, predicate:Predicate) -> None:
        self.wherePred = predicate
    
    def run(self, tableManager:TableManager) -> Res[Table, Exception]:
        return Res.Ok(tableManager
        ).flatMap(self._runFromClause
        ).flatMap(self._runWhereClause
        ).flatMap(self._runSelectClause)

    def _runFromClause(self, tableManager:TableManager) -> Res[Table, Exception]:
        # vvv this DOES stop as soon as it fails because it's a map so it's evaluated lazily inside toOverallList
        if (tables := tableManager.getTables(self.tableNames)).isErr(): return tables
        
        tables :list[Table] = tables.unwrap()
        firstTable = tables[0]
        for table in tables[1:]:
            if (joinRes := firstTable.join(table, None)).isErr(): return joinRes
            firstTable   = joinRes.unwrap()
        
        return Res.Ok(firstTable)

    def _runSelectClause(self, table:Table) -> Res[Table, Schema.ColumnNameErr|Schema.ColumnNameCollisionErr]:
        return table.select(self.columnNames)

    def _runWhereClause(self, table:Table) -> Res[Table, Schema.ColumnNameErr|SQLDomain.DomainValueErr]:
        return table.where(self.wherePred) if self.wherePred else Res.Ok(table)