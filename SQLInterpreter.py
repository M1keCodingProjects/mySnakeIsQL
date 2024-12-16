from Utils        import compareCaseInsensitive
from SQLTable     import Table
from SQLParser    import *
from TableManager import TableManager

class SQLInterpreter:
    def __init__(self, tableManager:TableManager) -> None:
        self.parser, self.tableManager = SQLParser(), tableManager
    
    def parseAndRun(self, programText:str) -> Res[None, Exception]:
        if (parsingRes := self.parse(programText)).isErr(): return parsingRes
        return self.run()
    
    def parse(self, programText:str) -> Res[None, Exception]:
        return self.parser.parse(programText)
    
    def run(self) -> Res[None, Exception]:
        print("Running query..")
        if (runRes := self.parser.parsedQuery.run(self.tableManager)).isErr(): return runRes
        
        print(runRes.unwrap())
        return Res.Ok(None)
    
#TODO: rewrite all of this using a state machine.
class UserInputCommand(StrEnum):
    QuitProgram = "EXIT"

def main():
    print("Welcome to my Snake is QL, a very bad SQL interpreter written in Python.")
    tableManager = TableManager.create("Student", "Exam", "Course").unwrap()
    interpreter  = SQLInterpreter(tableManager)

    while True:
        nextLine    = ""
        programText = ""
        print(
            f"Write your query below, making sure to end it with a semicolon, then press Enter to run the query." +
            f"\nTo fully quit the program write \"{UserInputCommand.QuitProgram}\" and hit Enter again.\n")
        
        while True:
            if not (nextLine := input("").strip()): continue
            if compareCaseInsensitive(nextLine, UserInputCommand.QuitProgram):
                print("User has quit the program.")
                return
            
            programText += ' ' + nextLine
            if ';' not in nextLine: continue
            
            print("\nQuery registered..")
            queryStatus    = interpreter.parseAndRun(programText)
            queryHasFailed = queryStatus.isErr()
            print(f"Query status: {'un' * queryHasFailed}successful.")
            
            if queryHasFailed: print(queryStatus.err)
            print(); break

if __name__ == '__main__': main()