# Fibonacci via Lambda Calculus - Implementation Plan

## Goal
Create a test demonstrating Fibonacci number generation using **pure lambda calculus** - no built-in arithmetic, no named recursion, only lambda functions.

## Background

Lambda calculus is a formal system for expressing computation based only on:
- **Abstraction**: `(lambda (x) body)` - creating functions
- **Application**: `(f arg)` - applying functions to arguments

### Key Concepts Used

#### 1. Church Numerals
Numbers encoded as functions. A Church numeral `n` takes a function `f` and a value `x`, and applies `f` to `x` exactly `n` times:
- `0 = λf.λx.x` (apply f zero times)
- `1 = λf.λx.(f x)` (apply f once)
- `2 = λf.λx.(f (f x))` (apply f twice)
- `n = λf.λx.(f (f ... (f x)))` (apply f n times)

#### 2. Church Booleans
- `TRUE = λx.λy.x` (returns first argument)
- `FALSE = λx.λy.y` (returns second argument)

#### 3. Pairs
- `CONS = λx.λy.λm.((m x) y)` (create pair)
- `CAR = λz.(z TRUE)` (first element)
- `CDR = λz.(z FALSE)` (second element)

#### 4. Arithmetic Operations
- **Successor**: `SUCC = λn.λf.λx.(f ((n f) x))`
- **Addition**: `ADD = λm.λn.λf.λx.((m f) ((n f) x))`

## Implementation Approach: Iterative Fibonacci

We use an **iterative approach** that leverages the inherent iteration capability of Church numerals. This is more elegant than using the Y combinator and avoids recursion depth issues.

### The Key Insight

A Church numeral `n` is essentially an iterator - it applies a function `f` exactly `n` times:
```
n = λf.λx.(f (f (f ... (f x))))
```

### The Algorithm

1. **Start** with pair `(fib(0), fib(1)) = (0, 1)`
2. **Transform**: Apply `FIB_STEP: (a, b) -> (b, a+b)`
3. **Iterate**: Apply `FIB_STEP` exactly `n` times using Church numeral iteration
4. **Extract**: Get the first element of the resulting pair

```
FIB_STEP = λp.(CONS (CDR p) (ADD (CAR p) (CDR p)))
FIB_INIT = (CONS 0 1)
FIB = λn.(CAR ((n FIB_STEP) FIB_INIT))
```

### Example: Computing fib(5)

```
Start:        (0, 1)
After step 1: (1, 1)    # (1, 0+1)
After step 2: (1, 2)    # (1, 1+1)
After step 3: (2, 3)    # (2, 1+2)
After step 4: (3, 5)    # (3, 2+3)
After step 5: (5, 8)    # (5, 3+5)
Result:       5         # CAR of (5, 8)
```

## Files Created

- `/claude/PLAN.md` - This plan document
- `/claude/test_fibonacci_lambda.py` - Standalone test file with comprehensive documentation

## Test Results

All tests pass, verifying:
- fib(0) = 0
- fib(1) = 1
- fib(2) = 1
- fib(3) = 2
- fib(4) = 3
- fib(5) = 5
- fib(6) = 8
- fib(7) = 13
- fib(8) = 21
- fib(9) = 34
- fib(10) = 55

## Why This Approach is Pure Lambda Calculus

1. **No built-in numbers** - Only Church numerals (lambda functions)
2. **No built-in arithmetic** - Addition defined via Church numeral composition
3. **No named recursion** - Uses iteration via Church numeral application
4. **No special forms** - Only lambda abstraction and application

The only "impurity" is the `TO_INT` conversion function which uses the `+` operator to convert Church numerals back to Python integers for assertion testing. This is purely for verification and not part of the Fibonacci computation itself.
