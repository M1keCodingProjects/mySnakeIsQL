from Utils     import Res
from SQLTable  import *
from SQLDomain import parseDomain

class TableManager:
    def __init__(self, loadedTables:dict[str, Table]) -> None:
        """ Private constructor """
        self.loadedTables = loadedTables
    
    def create(*tablesToLoad:str) -> Res[Self, Exception]:
        """ Static """
        return Res.toOverallDict({ name.lower() : loadTable(name) for name in tablesToLoad }).map(TableManager)

    def getTable(self, name:str) -> Res[Table, Exception]:
        return Res.wrap(lambda : self.loadedTables[name.lower()]
        ).mapErr(lambda _ : Exception(f"Table \"{name}\" either isn't in the database or hasn't been loaded."))

    def getTables(self, names:list[str]) -> Res[list[Table], Exception]:
        return Res.toOverallList(map(self.getTable, names))

class SubfolderAccessErr(CustomErr):
    MSG = "Table access paths must always be plain file names and cannot contain the \"/\" character"
    def __init__(self, path:str) -> None:
        super().__init__(f"provided path:\"{path}\"")

class UnknownTableErr(CustomErr):
    MSG = "Unknown table"
    def __init__(self, tableName:str) -> None:
        super().__init__(f"Couldn't recognize \"{tableName}\" as one of the available tables in the database")

def retrieveRawTableFromLoc(filename:str) -> Res[str, SubfolderAccessErr|UnknownTableErr]:
    # Prevent subfolder access:
    if '/' in filename: return Res.Err(SubfolderAccessErr(filename))

    with open(f"./Tables/{filename}.csv") as fd:
        return Res.wrap(fd.read).mapErr(lambda e : UnknownTableErr(filename))

def loadTable(name:str) -> Res[Table, Exception]:
    if (tableRows := retrieveRawTableFromLoc(name)).isErr(): return tableRows
    tableRows = tableRows.unwrap().split('\n')

    columnNames  = tableRows[0].split(",")
    typeMetadata = tableRows[1].split(",")
    if (columnsAmt := len(columnNames)) != len(typeMetadata):
        return Res.Err(Exception("Invalid schema: the amount of column names and domains must match."))

    schema = Schema()
    for columnName, domainStr in zip(columnNames, typeMetadata):
        if (domain := parseDomain(columnName, domainStr)).isErr(): return domain
        schema.addColumn(domain.unwrap())
    
    #TODO: check for collisions in the schema domain names

    instance = []
    for entry in tableRows[2:]:
        entryValues = entry.split(',')
        if (rowSize := len(entryValues)) != columnsAmt: return Res.Err(Exception(
            f"Row length does not match table schema, expected {columnsAmt} cells but got {rowSize}."))
    
        for valueStr, (_, domain) in zip(entryValues, schema.iterIdsAndDomains()):
            if (value := domain.parseValue(valueStr)).isErr(): return value
            instance.append(value.unwrap())
    
    return Res.Ok(Table(name, schema, instance))

def main() -> None:
    print(TableManager.create("Student").unwrap().loadedTables["student"].name)

if __name__ == "__main__": main()