# Quail : A Unit Testing Utility for the Flyable Compiler

---
**But, what is a quail?** [That's a quail.](ressources/quail.jpg)
So cute 🥺

## The idea behind Quail:

* The purpose of Quail is to be an easy to use, expandable and developper friendly framework to write unit tests for the
  Flyable compiler. It is built on top of pytest to have access to its vast set of tools and to integrate elegantly with
  IDEs

## What are Quail Tests?

Quail Tests are the meat and bones of the Quail unit testing utility. They represent

## How do they work

They operate, in their most basic form, by:

1. Using the python interpreter to:
    1. Compile the lines of code in the test
    2. Running the test and saving the output of the `stdout` (standard out)
2. Using the flyable compiler to:
    1. Compile the lines of code in the test
    2. Running the test and saving the output of the `stdout` (standard out)
4. Comparing those outputs

## Anatomy of a Quail Test

First, let's look a typical Quail Test and analyse it:

```python
# Quail-test:new
"""
Name: basic_addition
Flyable-version: v0.1a1
Description: Test the addition operator on int
"""
# Quail-test:start
0 + 0  # Quail-assert: eq 0
0 + 1  # Quail-assert: eq 1
1 + 1  # Quail-assert: eq 2
-10 + 23  # Quail-assert: eq 13
# Quail-test:end
```

For now, let's ignore the weird comments starting with `# Quail-...` and focus on their content and overall structure.
Quail tests are separated in multiple sections:

1. The information section
2. The test body section

Let's look at them in further details

### The information section

This section is the first section of every Quail test and contains all the metadata related to the test.  
In our example, it's this part:

```python
"""
Name: basic_addition
Flyable-version: v0.1a1
Description: Test the addition operator on int
"""
```

As we can see, this section is placed in a python multiline string and contains the following:

* The `Name` tag followed by the name of the test (ex: `basic_addition`)
* The `Flyable-version` followed by the version of the Flyable compiler it's testing (ex: `v0.1a1`)
* A `Description` tag followed by the description of the what the Quail Test is, well... testing (
  ex: `Test the addition operator on int`)

### The body section

This section contains what really matters, _the lines of code to test_ !
In our example, it's this part:

```python
0 + 0  # Quail-assert: eq 0
0 + 1  # Quail-assert: eq 1
1 + 1  # Quail-assert: eq 2
-10 + 23  # Quail-assert: eq 13
```

It's the content of this section that will be compiled and ran by the python interpreter and the flyable compiler to see
if their outputs match at runtime. But how can we compare the stdout if there's no print calls? And, most of all, what's
up with those `# Quail-assert:...` anyway? Those are really good questions and I feel like it's time to address them!

### Quail tags

Let's come back to those weird comments that start with `# Quail-...`. They are called Quail tags and are part of what
makes Quail so flexible. Each Quail tag follow a specific syntax:  
`# Quail-<tag_type>:<tag_name> [value]`

Currently, they come in one of two types, **Quail-test** tags and **Quail-assert** tags.

#### Quail-test tags

`Quail-test` tags allow the Quail Parser to know how the test is divided and parse the correct sections at the correct
time. In our example, it's those:

```python
# Quail-test:new
# Quail-test:start
# Quail-test:end
```

To see every Quail-test tag and its effect, see [The list of Quail-test tags](Quail-test_tags.md)

#### Quail-assert tags

`Quail-assert` tags tell the Quail Parser how to modify the current line to test something in particular. They also help
to remove boilerplate code and make the test more readable. In our example, it's those:

```python
# Quail-assert: eq 0
# Quail-assert: eq 1
# Quail-assert: eq 2
# Quail-assert: eq 13
```

To see every Quail-assert tag and its effect, see [The list of Quail-assert tags](Quail-assert_tags.md)

## How can I make my own?

Let's say I want to write a new test suite to test how _Flyable_ handles **lists** with Quail.

There are two ways of doing this, one automatically and one manually

### Automatically

1. I go to the folder _Flyable/tests/_ and run the _make_quail_test.py_ file
2. I use the Quail cli
   > |Quail> new liste  
   > Do you want to proceed to create Quail test suite with those informations ([Y], N)  
   > name = liste  
   > add_place_holder_test = True   
   > |Quail> y  
   > Done!
3. I go to the folder _Flyable/tests/unit_tests/liste/body_liste.py_ to write my Quail tests
4. I go to the folder _Flyable/tests/unit_tests/liste/test_liste.py_ to run the Quail test I wrote using pytest

















