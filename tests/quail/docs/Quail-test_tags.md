### A List of every Quail-test tags and their effect

> `Quail-test` tags allow the Quail Parser to know how the test is divided and parse the correct sections at the correct
> time.

> Legend:  
> \<value> → required value  
> [value] → optional value  
> (value1 | value2 | value3) → one of them, and one is required  
> (value1 | [value2 | value3]) → one of them but value1 is the default if none are given

1. new (runtime | [compile | both])
    * This tag is required at the start of each Quail test
    * If its value is compile, will do nothing for now (Quail test targeting compilation are coming soon)
    * After this tag must be the [Information Section](README.md#the-information-section)
2. start
    * This tag indicates the start of the [Test Body Section](README.md#the-body-section)
3. end
    * This tag is required at the end of each Quail test