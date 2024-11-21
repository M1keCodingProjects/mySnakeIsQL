from SQLParser import *
from TableManager import Table

class SQLInterpreter:
    def __init__(self, tables:dict[str, Table]) -> None:
        self.parser = SQLParser()
        self.tables = tables
    
    def parseAndRun(self, programText:str) -> Res[None, Exception]:
        if (parsingRes := self.parse(programText)).isErr(): return parsingRes
        return self.run()
    
    def parse(self, programText:str) -> Res[None, Exception]:
        return self.parser.parse(programText)
    
    def run(self) -> Res[None, Exception]:
        print("Running query..")

        runRes :Res[Table, Exception] = Res.wrap(
            lambda tableName : self.tables[tableName],
            self.parser.parsedQuery["table"]
        ).flatMap(lambda table : table.where(self.parser.parsedQuery["where"]) if self.parser.parsedQuery["where"] else table
        ).flatMap(lambda table : table.select(self.parser.parsedQuery["selectedColumns"]))
        
        if runRes.isErr(): return runRes

        print(runRes.unwrap())
        print("Query status: successful.\n")
        return Res.Ok(None)
    
#TODO: rewrite all of this using a state machine.
class UserInputCommand(StrEnum):
    QuitProgram = "EXIT"

def main():
    print("Welcome to my Snake is QL, a very bad SQL interpreter written in Python.")

    # load tables:
    tables = {
        "STUDENT" : loadTable("Student").unwrap(),
    }
    interpreter = SQLInterpreter(tables)

    while True:
        nextLine    = ""
        programText = ""
        print(
            f"Write your query below, making sure to end it with a semicolon(;), then press Enter to run the query." +
            f"\nTo fully quit the program write \"{UserInputCommand.QuitProgram}\" and hit Enter again.\n")
        
        while True:
            match nextLine := input("").upper().strip():
                case UserInputCommand.QuitProgram: return
                case "": continue
                case _:
                    programText += ' ' + nextLine
                    if ';' not in nextLine: continue
                    
                    print("\nQuery registered..")
                    interpreter.parseAndRun(programText).unwrap()
                    break

if __name__ == '__main__': main()