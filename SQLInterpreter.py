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
        ).map(lambda table : table.select(self.parser.parsedQuery["selectedColumns"])
        ).flatten()
        if runRes.isErr(): return runRes

        print(runRes.unwrap())
        print("Query status: successful.\n")
        return Res.Ok(None)
    
# Please rewrite all of this using a state machine.
class UserInputCommand(StrEnum):
    LaunchQuery = "RUN",
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
            f"Write your query below, then once it's ready write \"{UserInputCommand.LaunchQuery}\" " +
            f"and hit Enter again.\nTo fully quit the program write \"{UserInputCommand.QuitProgram}\" " +
            "and hit Enter again.\n")
        
        while True:
            match nextLine := input("").upper().strip():
                case "": continue
                case UserInputCommand.QuitProgram: return
                case UserInputCommand.LaunchQuery:
                    print("\nQuery registered..")
                    interpreter.parseAndRun(programText).unwrap()
                    break

                case _: programText += ' ' + nextLine

if __name__ == '__main__': main()