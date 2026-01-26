# Chapter 1: The Substitution Model

This chapter builds a working interpreter in about sixty lines of Python. The interpreter is based on a single idea: computation is the mechanical replacement of symbols. When you call a function, you substitute arguments into the body. When you reference a variable, you substitute its value. When you evaluate a conditional, you pick one branch and discard the other. By the end of the chapter, you'll have an interpreter that handles variables, conditionals, functions, recursion, and higher-order functions—enough to compute Fibonacci numbers, enough to trace any expression step by step on paper.

---

## What Is Computation?

Computation is the systematic transformation of symbols according to rules. When you see `(2 + 3) * 4`, you know to:

1. Evaluate the parenthesized expression first: `2 + 3` becomes `5`
2. Multiply the result by `4`: `5 * 4` becomes `20`

The symbols `(2 + 3) * 4` transformed into `20` through the application of rules you learned in elementary school. Programming languages work the same way, with richer sets of rules. The evaluator (or interpreter) is the engine that applies these rules. Our goal is to understand what rules are needed and how they interact.

---

## Primitives and Symbols

Every language needs primitives—irreducible elements that evaluate to themselves. In our language, integers are primitives:

```
> 1
1

> 42
42
```

When the evaluator encounters `1`, it returns `1`. No transformation needed.

Symbols are names that refer to values. The symbol `+` refers to the addition operation. The symbol `x` might refer to `2`, if we've defined it that way. When the evaluator encounters a symbol, it looks up the value.

---

## The Evaluate Function

Let's build an interpreter for a subset of Scheme—small enough to fit in sixty lines, powerful enough to compute Fibonacci numbers.

We'll represent Scheme's parenthesized expressions as Python tuples. Where Scheme writes `(+ 2 3)`, we'll write `("+", 2, 3)`. This lets us skip parsing and focus on evaluation.

The skeleton of our evaluator:

```python
def evaluate(expression):
    # For primitives, return as is.
    if isinstance(expression, int) or callable(expression):
        return expression

    # For symbols, do a look-up.
    elif isinstance(expression, str):
        return definitions[expression]

    # For tuples, handle special forms or apply procedures.
    elif isinstance(expression, tuple):
        # ... handle compound expressions
        pass
```

Every expression falls into one of three categories:

1. **Primitives** (integers, procedures): return unchanged
2. **Symbols** (names): look up their meaning
3. **Compound expressions** (tuples): evaluate according to rules

Where do symbols get their meaning? From a dictionary:

```python
definitions = {
    "+": lambda x, y: x + y,
    "*": lambda x, y: x * y,
    "-": lambda x, y: x - y,
    "/": lambda x, y: x / y,
    "=": lambda x, y: x == y,
    "<": lambda x, y: x < y,
    ">": lambda x, y: x > y,
}
```

This is the language's initial vocabulary. When we evaluate `"+"`, we get back the addition function.

---

## Special Forms: Define, If, Lambda

Not everything follows the "evaluate then apply" pattern. Some constructs have special evaluation rules. These are *special forms*.

**define** creates new bindings:

```python
if expression[0] == "define":
    definitions[expression[1]] = evaluate(expression[2])
    return None
```

When we write `("define", "x", 2)`, we store the value `2` under the name `"x"`.

**if** implements conditional evaluation:

```python
if expression[0] == "if":
    if evaluate(expression[1]):
        return evaluate(expression[2])
    return evaluate(expression[3])
```

Crucially, `if` only evaluates one branch—either the "then" clause or the "else" clause, never both.

**lambda** creates new procedures:

```python
if expression[0] == "lambda":

    def substitute(expr, name, value):
        if expr == name:
            return value
        elif isinstance(expr, tuple):
            return tuple([substitute(term, name, value) for term in expr])
        return expr

    def procedure(*arguments):
        names = expression[1]
        body = expression[2]

        for i, argument in enumerate(arguments):
            name = names[i]
            body = substitute(body, name, argument)

        return evaluate(body)

    return procedure
```

This is where the substitution model reveals itself. When we create a procedure with `("lambda", ("x",), ("*", "x", "x"))`, we're defining a transformation: take the body and, when called with an argument, substitute that argument for every occurrence of `"x"`, then evaluate the result.

---

## Procedure Application

When we see `("+", 2, 3)`, we need to:

1. Evaluate the operator (`"+"`) to get a procedure
2. Evaluate each operand (`2`, `3`) to get arguments
3. Apply the procedure to the arguments

```python
proc = evaluate(expression[0])
args = [evaluate(expr) for expr in expression[1:]]
return proc(*args)
```

Let's trace through `("+", 2, 3)`:

```
evaluate(("+", 2, 3))
  proc = evaluate("+")         → definitions["+"] → <addition function>
  args = [evaluate(2), evaluate(3)] → [2, 3]
  return proc(*args)           → (lambda x, y: x + y)(2, 3) → 5
```

The recursion is key. `evaluate` calls itself to process the operator and operands, bottoming out when it hits primitives.

---

## Putting It Together

Here's the complete evaluator:

```python
definitions = {
    "+": lambda x, y: x + y,
    "*": lambda x, y: x * y,
    "-": lambda x, y: x - y,
    "/": lambda x, y: x / y,
    "=": lambda x, y: x == y,
    "<": lambda x, y: x < y,
    ">": lambda x, y: x > y,
}


def evaluate(expression):
    # For primitives, return as is.
    if isinstance(expression, int) or callable(expression):
        return expression

    # For symbols, do a look-up.
    elif isinstance(expression, str):
        return definitions[expression]

    # For tuples, separate special forms vs application of procedures.
    elif isinstance(expression, tuple):
        if expression[0] == "define":
            definitions[expression[1]] = evaluate(expression[2])
            return None

        elif expression[0] == "if":
            if evaluate(expression[1]):
                return evaluate(expression[2])
            return evaluate(expression[3])

        elif expression[0] == "lambda":

            def substitute(expr, name, value):
                if expr == name:
                    return value
                elif isinstance(expr, tuple):
                    return tuple([substitute(term, name, value) for term in expr])
                return expr

            def procedure(*arguments):
                names = expression[1]
                body = expression[2]

                for i, argument in enumerate(arguments):
                    name = names[i]
                    body = substitute(body, name, argument)

                return evaluate(body)

            return procedure

        # Look up procedure and apply to evaluated arguments.
        proc = evaluate(expression[0])
        args = [evaluate(expr) for expr in expression[1:]]
        return proc(*args)
```

Sixty-one lines. A language with integers, arithmetic, conditionals, variables, and procedures.

---

## Fibonacci: A Proof It Works

The true test is whether we can express interesting computations. The Fibonacci sequence requires arithmetic, conditionals, and recursive procedure calls:

```python
fibonacci = (
    "lambda", ("n",),
    (
        "if", ("<", "n", 2),
            1,
            ("+", ("fibonacci", ("-", "n", 2)), ("fibonacci", ("-", "n", 1))),
    ),
)

evaluate(("define", "fibonacci", fibonacci))

results = [evaluate(("fibonacci", i)) for i in range(10)]
# [1, 1, 2, 3, 5, 8, 13, 21, 34, 55]
```

It works. Let's trace `("fibonacci", 3)`:

```
evaluate(("fibonacci", 3))
  # Substitute n=3 into the body:
  ("if", ("<", 3, 2), 1, ("+", ("fibonacci", ("-", 3, 2)), ("fibonacci", ("-", 3, 1))))

  # 3 < 2 is false, so evaluate the else branch:
  ("+", ("fibonacci", 1), ("fibonacci", 2))

  # fibonacci(1): 1 < 2 is true, return 1
  # fibonacci(2): 2 < 2 is false, so ("+", ("fibonacci", 0), ("fibonacci", 1))
  #   fibonacci(0) = 1, fibonacci(1) = 1, so 1 + 1 = 2

  # Back to our expression: 1 + 2 = 3
```

The entire computation unfolds through substitution—symbols replacing symbols until we reach a value.

---

## Conclusion

The substitution model is complete. You now have a mental model precise enough to execute programs by hand—no hidden machinery, no mysterious runtime, just symbols replacing symbols until a value emerges. The interpreter we built is small, but it handles the core of what any language must handle. In the next chapter, we'll see where this model breaks.
