# my Snake is QL - a very bad SQL interpreter written in Python
Eventually someone will write a good description here..

## How to run a Query
- Run the `SQLInterpreter.py` file
- Type your query, even using multiple lines:
  
  ```SQL
  select SId, Name
  from Student
  ```
- Press `Enter` again and write `run` on its own line:

  ```SQL
  select SId, Name
  from Student
  run
  ```
- Press `Enter` again to launch query
- Once a query is done, if successful, you will be prompted to write another one: if you wish to **quit** the program instead, write `exit`
- For now, any kind of **error** in the process fully halts the program.

## Examples:
### Select *:
```SQL
select *
from Student
```