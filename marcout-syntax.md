# MARCout Syntax

----
## MARCout Export Definition Page Syntax

An Export Definition page is divided into blocks by the following headers:

DESCRIPTION--------------------------------------
Reference notes to inform the Export definition editor / reader.

KNOWN PARAMETERS---------------------------------
Named expected values available at export time. Characteristically defined by the
holder of the records being exported. Used in Expressions.

JSON EXTRACTED PROPERTIES------------------------
Named node identification expressions that retrieve content from an exported
record. Dependent on the JSON format of the record. Used in Expressions.

FUNCTIONS----------------------------------------
Named utility functions with signature information. Used in Expressions.

MARC FIELD TEMPLATES------------------------------------
Specific forms for constructing MARC 21 LDR and Field expressions.





----
## EXPRESSIONS
MARCout defines a simple "expression" syntax for defining exported data. 
Expressions are composed of:

    - MARCout keywords and operators: a limited set of reserved words, single
        characters, and phrases that provide simple expression semantics.

    - Literal content: fixed strings. Always enclosed in single quotes.

    - Source record extraction expressions: named JSON node syntax expressions
        found in the JSON EXTRACTED PROPERTIES block of a MARCout file.

    - Function calls: functions whose signatures are listed in the FUNCTIONS 
        block of a MARCout file.

    - Parameters: parameters whose names are listed in the KNOWN PARAMETERS
        block of a MARCout file

GEEKLY DISCLAIMER:
Programmers will be disappointed with MARCout expression semantics & syntax.
They will feel immediately frustrated because their normal modes of
thought and work are ruthlessly unsupported. So, it's important to emphasize
that MARCout EXPRESSIONS WERE NEVER INTENDED TO BE A SCRIPTING LANGUAGE.
They are only a simplistic declarative way to state common-case rules and
directives for composing MARC export content.

The keywords and operators, in particular, very deliberately leave out some
things that programmers would expect. For example:

    - Expression keywords and operators do not support IF/ELSE conditionals.

    - No grouping brackets (except for the parentheses in function calls).

    - There is no proper handling of boolean logic: no `AND`, `OR`,
        or `NOT` operators; the union of `IS FALSE` and `IS TRUE` does not
        exhaust the value space of expressions (those keywords are limited
        to values that *explicitly* indicate true or false conditions).

    - No arithmetic.

    - No date comparisons.

    - And so on.

Take heart, though, programmers: the extensibility loophole is that MARCout
permits you to define your own functions and add them to your MARCout record
exporter code. NB: don't forget to add them to the MARCout export definition 
FUNCTIONS block too.

MARCout EXPRESSION SPECIFIC VALUES:

    - `PRESENT`: (for JSON node expressions and parameters.) A MARCout
        expression evaluates as `PRESENT` if it does not encounter a
        "not found" or "undefined" problem.

        Note that an expression will evaluate as `PRESENT` irrespective of
        its value. A value of None, JSON null, or an empty string, in
        particular, does not prevent, or in any way affect, evaluation as
        `PRESENT`.

    - `FALSE`: a MARCOUT expression evaluates as `FALSE` if it is `PRESENT`
        and has one of the following values: 

            - `false` (if boolean),

            - case-insensitive "no" or case-insensitive "false" (if string), 

            - 0 (if number)

        Note! the values 'F' and 'N' do NOT evaluate as `FALSE`, because 
        they could reasonably signify something else. If you have a "Y/N"
        or "T/F" enumeration in a field in your JSON, test for the
        explicit value.

    - `TRUE`: a MARCout expression evaluates as `TRUE` if it is `PRESENT`
        and has one of the following values: 

            - `true` (if boolean),

            - case-insensitive "yes" or case-insensitive "true" (if string), 

            - 1 (if number)

        Note! the values 'T' and 'Y' do NOT evaluate as `FALSE`, because 
        they could reasonably signify something else. If you have a "Y/N"
        or "T/F" enumeration in a field in your JSON, test for the
        explicit value.

    - `EMPTY`: a MARCout expression evaluates as `EMPTY` if it is `PRESENT`
        and is one of the following:

            - an empty string

            - a whitespace string

            - a collection of type `list`, `tuple`, `dict`, or `set`, with 
                length of zero.


MARCout EXPRESSION KEYWORDS AND OPERATORS:
This syntax is intended to be simple to learn and not confusing to sight-read.
It facilitates composing extracted content from the record to export with
literal values and function calls.

    - `IS`: infix operator that compares two sub-expressions for equality. 
        Equivalent to `==` in Python.

    - `IS NOT`: infix operator that compares two sub-expressions for inequality. 
        Equivalent to `!=` in Python.

    - `IS TRUE`: postfix operator that resolves to True if the preceding
        expression is a MARCout value for `TRUE`.

    - `IS FALSE`: postfix operator that resolves to True if the preceding
        expression is a MARCout value for `FALSE`.

    - `HAS VALUE`: postfix operator that resolves to True if the preceding 
        expression is PRESENT and not `EMPTY`. In other words, the expression
        has meaning over and above the ambiguous empty values.

    - `HAS NO VALUE`: postfix operator that resolves to True if the preceding
        expression is not `PRESENT`, or, if `PRESENT`, is `EMPTY`.

    - `NOTHING`: alias (non-operator) keyword for generation of an empty value.
        Depending on context, makes an empty string, or a non-value such as 
        Python `None` or JSON `null`.

    - `STARTS WITH`: operator for string values. Resolves to True if the
        preceding string starts with the subsequent string.

    - `CONTAINS`: operator for string values. Resolves to True if the
        preceding string starts with the subsequent string.

    - `+`: the concatenation operator for string values. Does NOT represent
        numeric addition, date addition, etc.

