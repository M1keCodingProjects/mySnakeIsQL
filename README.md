# my Snake is QL - a very bad SQL interpreter written in Python
Eventually someone will write a good description here..

## How to run a Query
- Run the `SQLInterpreter.py` file
- Type your query, even using multiple lines, and make sure it ends with a semicolon:
  
  ```SQL
  select SId, Name
  from Student;
  ```
- Press `Enter` to run the query
- Once a query is done, if successful, you will be prompted to write another one: if you wish to **quit** the program instead, write `exit`

## Examples:
### Select all the columns:
```SQL
select *
from Student;
```
### Select where:
Select only some entries based on a simple predicate. So far, the program only supports a simple comparison predicate in the form `Attribute ComparisonOperator Value`:
```SQL
select Name
from Student
where SId < 3;
```

String literal values are also accepted:
```SQL
select Name
from Student
where Name = "John Doe";
```