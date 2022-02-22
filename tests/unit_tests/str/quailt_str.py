"""Module where str body tests are created"""

# Quail-test:new
"""
Name: empty_str_creation
Flyable-version: v0.1a1
Description: Test that the result of "" equals the result of calling str()
"""
# Quail-test:start
litteral_str = ""
litteral_str_by_method = str()
litteral_str == litteral_str_by_method  # Quail-assert: True
# Quail-test:end


# Quail-test:new
"""
Name: str_equality
Flyable-version: v0.1a1
Description: Test that two strings with the same values are equals
"""
# Quail-test:start
a = ""
a == "" # Quail-assert: True

b = "Hello"
b == "Hello" # Quail-assert: True
b == b # Quail-assert: True

c = "Hello"
b == c # Quail-assert: True

d = "hello"
c == d # Quail-assert: False

# Quail-test:end


# Quail-test:new
"""
Name: len_str
Flyable-version: v0.1a1
Description: Test that the len function works properly on strings
"""
# Quail-test:start
msg = "hello world!"
len(msg) == 12  # Quail-assert: True
msg2 = ""
len(msg2) == 1  # Quail-assert: False
len(msg2) == 0  # Quail-assert: True
# Quail-test:end


# Quail-test:new
"""
Name: concatenation
Flyable-version: v0.1a1
Description: Test the string concatenation functions
"""
# Quail-test:start
world = "World!"
"Hello " + world + " " + str(42)  # Quail-assert: eq 'Hello World! 42'
'Hello {} {}'.format(world, 42)  # Quail-assert: eq 'Hello World! 42'
f"Hello {world} "  # Quail-assert: eq 'Hello World! '
"%s %s %s" % ('Hello', world, 42)  # Quail-assert: eq 'Hello World! 42'
# Quail-test:end


# Quail-test:new
"""
Name: unicode_str
Flyable-version: v0.1a1
Description: Test string manipulation with unicode characters
"""
# Quail-test:start
checkmark = u'\u2713'
checkmark == "✓" # Quail-assert: True

checkmark2 = "✓"
checkmark == checkmark2 # Quail-assert: True

s = "This is a " + checkmark
s == "This is a ✓"

s2 = "This is another " + u'\u2713'
s2 == "This is another ✓" # Quail-assert: True

s3 = "(ノಠ益ಠ)ノ彡 ɹoʇıpƎ ʇxǝ⊥"
s3 == "(ノಠ益ಠ)ノ彡 ɹoʇıpƎ ʇxǝ⊥" # Quail-assert: True

s4 = "(ﾟ◥益◤ﾟ) T͕ͫe̱͛̀ͤx̦͓͓́ͬ̽̽ͨț̂͆͂ ̤̒̌ͦ̌Ȇ̻͈̇̚d̃̋ͥ̓i̼̓̃t̩̗̻̟̥̆̆̋̊̊o̭͍̠̩̪ͨͤr̠̪ͅ  (ʘ言ʘ╬)"
s4 == "(ﾟ◥益◤ﾟ) T͕ͫe̱͛̀ͤx̦͓͓́ͬ̽̽ͨț̂͆͂ ̤̒̌ͦ̌Ȇ̻͈̇̚d̃̋ͥ̓i̼̓̃t̩̗̻̟̥̆̆̋̊̊o̭͍̠̩̪ͨͤr̠̪ͅ  (ʘ言ʘ╬)" # Quail-assert: True
# Quail-test:end


# Quail-test:new
"""
Name: contains_str
Flyable-version: v0.1a1
Description: Test the in operator between strings
"""
# Quail-test:start
"" in "Hello World!" # Quail-assert: True
"d" in "Hello World!" # Quail-assert: True
"Hello " in "Hello World!" # Quail-assert: True
"Hello World!" in "Hello World!" # Quail-assert: True

"f" in "Hello World!" # Quail-assert: False
"d!w" in "Hello World!" # Quail-assert: False
"HelloWorld!" in "Hello World!" # Quail-assert: False
# Quail-test:end


# Quail-test:new
"""
Name: str_slicing
Flyable-version: v0.1a1
Description: Test the python slice operator
"""
# Quail-test:start
"Hello World!"[:5] == "Hello" # Quail-assert: True
"Hello World!"[6:] == "World!" # Quail-assert: True
"Hello World!"[:] == "Hello World!" # Quail-assert: True
"Hello World!"[0:0] == "" # Quail-assert: True
"Hello World!"[2:4] == "ll" # Quail-assert: True
"Hello World!"[:-7] == "Hello" # Quail-assert: True
"Hello World!"[-6:] == "World!" # Quail-assert: True
"Hello World!"[-6:-5] == "W" # Quail-assert: True

# Quail-test:end