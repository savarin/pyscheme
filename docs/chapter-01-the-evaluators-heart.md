# Chapter 1: The Evaluator's Heart

> *"The evaluator, which determines the meaning of expressions in a programming language, is just another program."*
> — Structure and Interpretation of Computer Programs

What does it mean to run a program?

This question sits at the foundation of computer science, yet most programmers never confront it directly. We write code, press a button, and something happens. The transformation from text to behavior feels like magic—or at least like someone else's problem.

In this chapter, we will dispel that magic. We will build, from scratch, a program that runs other programs. Along the way, we will discover a profound insight: **evaluation is recursion**. The same pattern that lets us compute factorials also lets us breathe life into code.

By the end of this chapter, you will understand the beating heart of every interpreter ever written. It is smaller than you think—and more beautiful.

---

## 1.1 The Shape of an Expression

Before we can evaluate programs, we need to understand what programs look like. Consider this arithmetic:

```
2 + 3
```

Simple enough. But how does a computer see it? The expression has structure: an operator (`+`) and two operands (`2` and `3`). We can represent this structure as a tree:

```
       +
      / \
     2   3
```

In Scheme—the language we'll implement—the same expression is written:

```scheme
(+ 2 3)
```

The operator comes first (prefix notation), followed by its arguments. This isn't just stylistic preference. It means every expression has the same shape: an operator, then operands. No precedence rules. No ambiguity.

For our interpreter, we'll represent Scheme expressions using Python tuples:

```python
("+", 2, 3)
```

The first element is the operator. The rest are arguments. Nested expressions become nested tuples:

```python
("+", ("*", 2, 3), 4)    # (+ (* 2 3) 4) → 10
```

Visually:

```
           +
          / \
         *   4
        / \
       2   3
```

This is our first key insight: **programs are trees**. Evaluation is the process of walking those trees.

---

## 1.2 What Is an Atom?

Not everything is a tree. At the leaves, we find atoms—the indivisible units of our language.

In Scheme, atoms include:

- **Numbers**: `1`, `42`, `-7`
- **Symbols**: `x`, `fibonacci`, `+`

Numbers are self-evaluating. When you ask "what is 42?", the answer is 42. There's nowhere deeper to go.

```python
>>> evaluate(1)
1

>>> evaluate(42)
42
```

Symbols are names that refer to values. When you ask "what is `x`?", the answer depends on what `x` has been defined to mean. We'll handle that shortly.

Here is the beginning of our interpreter:

```python
def evaluate(expression):
    # Numbers evaluate to themselves
    if isinstance(expression, int):
        return expression
```

Two lines. We can already evaluate half of all atoms.

---

## 1.3 The Definitions Dictionary

Where do names get their meanings?

Every programming language needs a place to store the association between names and values. In a full implementation, this is called an *environment*. For now, we'll use something simpler: a Python dictionary.

```python
definitions = {
    "+": lambda x, y: x + y,
    "-": lambda x, y: x - y,
    "*": lambda x, y: x * y,
    "/": lambda x, y: x / y,
    "=": lambda x, y: x == y,
    "<": lambda x, y: x < y,
    ">": lambda x, y: x > y,
}
```

The built-in operations are just Python functions. When our Scheme program uses `+`, it's ultimately calling Python's addition.

Now we can handle symbol lookup:

```python
def evaluate(expression):
    if isinstance(expression, int):
        return expression

    elif isinstance(expression, str):
        return definitions[expression]
```

When we see a string (a symbol), we look it up:

```python
>>> evaluate("+")
<function <lambda> at 0x...>
```

The symbol `"+"` evaluates to a function that adds things. The symbol is just a name; the function is what the name means.

---

## 1.4 The Recursive Leap

Here is where everything comes together.

We can evaluate atoms. But expressions aren't atoms—they're tuples containing other expressions. How do we evaluate `("+", 2, 3)`?

The insight is this: **to evaluate a compound expression, first evaluate its parts**.

```
   ("+", 2, 3)
        │
        ▼
   ┌─────────────────────────────────────────┐
   │  1. Evaluate "+"    →  <add function>   │
   │  2. Evaluate 2      →  2                │
   │  3. Evaluate 3      →  3                │
   │  4. Apply function  →  5                │
   └─────────────────────────────────────────┘
        │
        ▼
        5
```

This is recursion in its purest form. Evaluating a whole requires evaluating the parts. The parts might themselves be wholes. We keep going until we hit atoms.

Here is the code:

```python
def evaluate(expression):
    if isinstance(expression, int):
        return expression

    elif isinstance(expression, str):
        return definitions[expression]

    elif isinstance(expression, tuple):
        proc = evaluate(expression[0])          # Evaluate operator
        args = [evaluate(e) for e in expression[1:]]  # Evaluate arguments
        return proc(*args)                      # Apply
```

Read that carefully. The `evaluate` function calls itself—once for the operator, once for each argument. This is the recursive heartbeat.

Let's trace through `("+", ("*", 2, 3), 4)`:

```
evaluate(("+", ("*", 2, 3), 4))
│
├─► evaluate("+")  →  <add>
│
├─► evaluate(("*", 2, 3))
│   │
│   ├─► evaluate("*")  →  <multiply>
│   ├─► evaluate(2)    →  2
│   ├─► evaluate(3)    →  3
│   │
│   └─► multiply(2, 3) →  6
│
├─► evaluate(4)  →  4
│
└─► add(6, 4)  →  10
```

The evaluation proceeds depth-first. We dive all the way down to atoms, then bubble results back up. By the time we apply `add`, both arguments are already numbers.

---

## 1.5 The Core Loop

We now have a complete evaluator for arithmetic expressions:

```python
definitions = {
    "+": lambda x, y: x + y,
    "-": lambda x, y: x - y,
    "*": lambda x, y: x * y,
    "/": lambda x, y: x / y,
    "=": lambda x, y: x == y,
    "<": lambda x, y: x < y,
    ">": lambda x, y: x > y,
}

def evaluate(expression):
    if isinstance(expression, int):
        return expression

    elif isinstance(expression, str):
        return definitions[expression]

    elif isinstance(expression, tuple):
        proc = evaluate(expression[0])
        args = [evaluate(e) for e in expression[1:]]
        return proc(*args)
```

Fifteen lines. This is the skeleton upon which all interpreters are built.

The pattern is universal:

```
┌──────────────────────────────────────────────────┐
│                 evaluate(expr)                   │
├──────────────────────────────────────────────────┤
│                                                  │
│  Is expr an atom?                                │
│  ├── Number  →  return it                        │
│  └── Symbol  →  look it up                       │
│                                                  │
│  Is expr compound?                               │
│  └── Tuple   →  evaluate parts, combine results  │
│                                                  │
└──────────────────────────────────────────────────┘
```

This is what we mean by "the evaluator's heart." Every language feature we add—variables, conditionals, functions—will slot into this structure. The heart keeps beating; we just teach it new rhythms.

---

## 1.6 Defining Names

Arithmetic alone is limiting. We want to name things:

```scheme
(define x 2)
(+ x 3)        ; → 5
```

In Python tuples:

```python
("define", "x", 2)
("+", "x", 3)
```

The `define` form is our first *special form*. Unlike ordinary expressions, we don't evaluate all its parts the same way. We evaluate the value, but the name stays as a symbol—we're not looking it up, we're creating a new binding.

```python
elif isinstance(expression, tuple):
    if expression[0] == "define":
        name = expression[1]
        value = evaluate(expression[2])
        definitions[name] = value
        return None

    # ... rest of evaluation
```

Now:

```python
>>> evaluate(("define", "x", 2))
>>> evaluate(("+", "x", 3))
5
```

The name `"x"` is stored in `definitions`. Later, when we evaluate `("+", "x", 3)`, the symbol lookup finds `x → 2`.

Here is how the evaluation flows:

```
evaluate(("define", "x", 2))
│
├─► expression[0] == "define"  ✓
├─► name = "x"
├─► value = evaluate(2) → 2
├─► definitions["x"] = 2
└─► return None

evaluate(("+", "x", 3))
│
├─► proc = evaluate("+") → <add>
├─► args = [evaluate("x"), evaluate(3)]
│         = [definitions["x"], 3]
│         = [2, 3]
└─► add(2, 3) → 5
```

---

## 1.7 Conditionals

Programs need to make decisions. Scheme's `if` has this shape:

```scheme
(if predicate consequent alternative)
```

If the predicate is true, evaluate the consequent. Otherwise, evaluate the alternative.

```python
(if (= 1 1) 2 3)   ; → 2
(if (= 0 1) 2 3)   ; → 3
```

This is another special form. We can't evaluate all three branches—that would defeat the purpose. We evaluate the predicate first, then choose which branch to evaluate:

```python
elif expression[0] == "if":
    predicate = expression[1]
    consequent = expression[2]
    alternative = expression[3]

    if evaluate(predicate):
        return evaluate(consequent)
    else:
        return evaluate(alternative)
```

The `evaluate(predicate)` runs first. Based on the result, exactly one of the branches runs.

```
evaluate(("if", ("=", 1, 1), 2, 3))
│
├─► evaluate(("=", 1, 1))
│   ├─► proc = evaluate("=") → <equals>
│   ├─► args = [1, 1]
│   └─► equals(1, 1) → True
│
├─► True, so evaluate consequent
└─► evaluate(2) → 2
```

The alternative `3` is never evaluated. This matters more than you might think—we'll return to it in Chapter 6 when we discuss evaluation strategies.

---

## 1.8 Putting It Together

Here is our complete interpreter so far:

```python
definitions = {
    "+": lambda x, y: x + y,
    "-": lambda x, y: x - y,
    "*": lambda x, y: x * y,
    "/": lambda x, y: x / y,
    "=": lambda x, y: x == y,
    "<": lambda x, y: x < y,
    ">": lambda x, y: x > y,
}


def evaluate(expression):
    # Atoms
    if isinstance(expression, int):
        return expression

    elif isinstance(expression, str):
        return definitions[expression]

    # Compound expressions
    elif isinstance(expression, tuple):
        # Special form: define
        if expression[0] == "define":
            definitions[expression[1]] = evaluate(expression[2])
            return None

        # Special form: if
        elif expression[0] == "if":
            if evaluate(expression[1]):
                return evaluate(expression[2])
            return evaluate(expression[3])

        # Procedure application
        proc = evaluate(expression[0])
        args = [evaluate(e) for e in expression[1:]]
        return proc(*args)
```

Thirty lines. We have variables, arithmetic, comparisons, and conditionals. The only thing missing is the ability to create our own procedures.

That's what Chapter 3 is for.

---

## 1.9 The Substitution Model

Before we add functions, let's develop a mental model for what evaluation does.

When we evaluate `(+ 2 3)`, we can think of it as *substituting* values for symbols until nothing remains but the answer:

```
(+ 2 3)
   │
   │  substitute + with the add function
   ▼
(add 2 3)
   │
   │  apply the function
   ▼
   5
```

For a more complex expression:

```
(+ (* 2 3) 4)
   │
   │  substitute * with multiply
   ▼
(+ (multiply 2 3) 4)
   │
   │  apply multiply
   ▼
(+ 6 4)
   │
   │  substitute + with add
   ▼
(add 6 4)
   │
   │  apply add
   ▼
  10
```

This is the *substitution model* of evaluation. SICP introduces it as a first approximation—good enough to reason about simple programs, but not the full story.

> *"The purpose of the substitution is to help us think about procedure application, not to provide a description of how the interpreter really works."*
> — SICP, Section 1.1.5

The substitution model will guide us through the next two chapters. In Chapter 4, we'll discover where it breaks down—and why that matters.

---

## 1.10 Looking Back, Looking Forward

Let's reflect on what we've built.

We started with a question: what does it mean to run a program? The answer is a recursive function that does three things:

1. **Atoms** evaluate to themselves (numbers) or are looked up (symbols)
2. **Special forms** have custom evaluation rules
3. **Everything else** evaluates parts, then combines them

```
┌────────────────────────────────────────────────────┐
│                    EXPRESSION                      │
├───────────────┬───────────────┬────────────────────┤
│     Atom      │  Special Form │  Procedure Call    │
├───────────────┼───────────────┼────────────────────┤
│ Number → self │ define → bind │ 1. Eval operator   │
│ Symbol → look │ if → branch   │ 2. Eval arguments  │
│           up  │ lambda → ???  │ 3. Apply           │
└───────────────┴───────────────┴────────────────────┘
```

The `lambda` box is empty. That's our next destination.

But notice: the structure is complete. We won't change the fundamental shape of `evaluate`. Every feature we add—functions, closures, streams—will be a new clause in this same recursive structure.

This is the evaluator's heart. It has been beating since McCarthy's original Lisp in 1958. It beats in Python, JavaScript, Ruby. It will beat in whatever language comes next.

Learn this pattern, and you understand the essence of programming languages.

---

## Exercises

**1.1** Trace the evaluation of `("*", ("+", 1, 2), ("-", 5, 3))` step by step. Draw the tree and show how values bubble up.

**1.2** Our interpreter crashes on undefined symbols. Add an error message that tells the user which symbol wasn't found.

**1.3** Add a `not` operation to `definitions`. It should work like this:

```python
>>> evaluate(("not", ("=", 1, 2)))
True
>>> evaluate(("not", ("=", 1, 1)))
False
```

**1.4** Add an `and` special form that evaluates its arguments left to right and stops early if any is false. Why must this be a special form rather than a regular function?

**1.5** What happens if you evaluate `("if", ("=", 1, 1), ("+", 1, "undefined"), 0)`? What about `("if", ("=", 1, 2), ("+", 1, "undefined"), 0)`? What does this tell you about our `if` implementation?

---

## Summary

- Programs are trees. Evaluation is tree-walking.
- Atoms are the leaves: numbers self-evaluate; symbols are looked up.
- Compound expressions evaluate their parts recursively.
- Special forms (like `define` and `if`) have custom evaluation rules.
- The substitution model helps us reason about evaluation.
- The core evaluator is ~30 lines. Everything else builds on this foundation.

In the next chapter, we'll explore the `definitions` dictionary more deeply. Where do names live? What happens when the same name means different things in different places? The answers will transform our simple dictionary into something far more powerful: an environment.
