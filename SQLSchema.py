from Utils     import CustomErr, Res
from typing    import *
from SQLDomain import *

class Schema:
    class ColumnNameCollisionErr(CustomErr):
        MSG = "Column name collision"
        def __init__(self, columnName:str) -> None:
            super().__init__(f"reference to column \"{columnName}\" is ambiguous")

    class ColumnNameErr(CustomErr):
        MSG = "Unknown column"
        def __init__(self, columnName:str) -> None:
            super().__init__(f"a column called \"{columnName}\" is not present in the schema")

    def __init__(self) -> None:
        self.domains     :list[SQLDomain]      = []
        self.__positions :dict[str, list[int]] = {}

    def copy(self) -> Self:
        inst = Schema()
        inst.domains     = self.domains.copy()
        inst.__positions = self.__positions.copy()
        return inst

    def getColumnsAmount(self) -> int: return len(self.domains)

    def merge(left:Self, right:Self) -> Self:
        """Static"""
        mergedSchema = left.copy()
        for domain in right.domains: mergedSchema.addColumn(domain)
        
        return mergedSchema

    def addColumn(self, domain:SQLDomain) -> None:
        normalizedDomainName = domain.name
        if normalizedDomainName not in self.__positions: self.__positions[normalizedDomainName] = []
        self.__positions[normalizedDomainName].append(self.getColumnsAmount())
        self.domains.append(domain)
    
    def iterNames(self) -> KeysView[str]:
        return self.__positions.keys()

    def iterIdsAndDomains(self) -> Collection[tuple[int, SQLDomain]]:
        return enumerate(self.domains)

    def iterColumns(self) -> Collection[tuple[str, int, SQLDomain]]:
        """Beware performance"""
        return map(lambda column : (column[1].name, *column), self.iterIdsAndDomains())

    def getActualNames(self) -> Collection[str]:
        return map(lambda domain : domain.actualName, self.domains)

    def getIdAndDomain(self, name:str) -> Res[tuple[int, SQLDomain], "Schema.ColumnNameErr|Schema.ColumnNameCollisionErr"]:
        if (caseFoldedName := name.lower()) not in self.__positions: return Res.Err(Schema.ColumnNameErr(name))

        domainIds = self.__positions[caseFoldedName]
        if len(domainIds) > 1: return Res.Err(Schema.ColumnNameCollisionErr(name))
        
        return Res.Ok((domainIds[0], self.domains[domainIds[0]]))

    def __repr__(self) -> str:
        return "\n".join([f"Column #{cId} \"{name}\" : {domain}" for name, cId, domain in self.iterColumns()])

def main() -> None:
    schema = Schema()
    schema.addColumn(IntegerDomain("SId"))
    schema.addColumn(StringDomain("Name", 40))
    schema.addColumn(StringDomain("Name", 40))

    print(schema)

if __name__ == "__main__": main()