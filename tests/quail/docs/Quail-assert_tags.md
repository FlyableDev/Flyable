### A List of every Quail-assert tags and their effect

> `Quail-assert` tags tell the Quail Parser how to modify the current line to test something in particular. They also help
> to remove boilerplate code and make the test more readable.

> Legend:  
> \<value> → required value  
> [value] → optional value  
> (value1 | value2 | value3) → one of them, and one is required  
> (value1 | [value2 | value3]) → one of them but value1 is the default if none are given
> ... → the line before the tag

1. \-
    * Wraps the line in a print call:  
      `print(...)`
2. (eq | ==) \<otherValue>
    * Wraps the line in a print call adds an equality check  
      `print((...) == otherValue)`
3. True
    * Same as `eq`, but `otherValue = True`
4. False
    * Same as `eq`, but `otherValue = False`
5. raises [errorName]
    * Wraps the line in a try catch statement and checks for catches

   ```python
   try:
       ...
   except errorName:
       print(True)
   else:
       print(False)
   ```
