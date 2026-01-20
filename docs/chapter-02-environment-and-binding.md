# Chapter 2: Environment & Binding

> *"The environment is crucial, because it determines the context in which an expression should be evaluated."*
> — Structure and Interpretation of Computer Programs

In Chapter 1, we stored variable bindings in a Python dictionary called `definitions`. This was simple and it worked. But it hides a question that every programming language must answer:

**Where do names live?**

This chapter explores that question. We'll discover that a simple dictionary isn't enough—we need something that can handle multiple scopes, nested contexts, and the peculiar behavior of functions that remember where they came from.

By the end, you'll understand environments: the data structure that gives names their meaning.

---

## 2.1 The Trouble with Global State

Consider this Scheme program:

```scheme
(define x 10)
(define add-x (lambda (y) (+ x y)))
(add-x 5)    ; → 15
```

With our Chapter 1 interpreter, this works fine. The `definitions` dictionary holds both `x` and `add-x`, and when the function runs, it looks up `x` and finds `10`.

But what about this?

```scheme
(define x 10)
(define add-x (lambda (x) (+ x 1)))
(add-x 5)    ; → ???
```

We've used `x` as both a global variable and a function parameter. What should happen?

In our simple interpreter, `(add-x 5)` would:
1. Substitute `5` for `x` in the body `(+ x 1)`
2. Evaluate `(+ 5 1)`
3. Return `6`

That's correct! But we got lucky. Our substitution approach rewrites the expression before evaluation, so the parameter `x` shadows the global `x`. What happens if we try something trickier?

```scheme
(define x 10)
(define outer (lambda (x) (lambda () x)))
(define inner (outer 5))
(inner)    ; → should be 5, not 10
```

Here, `outer` returns a function that references `x`. When we call `(outer 5)`, the `x` inside the returned function should be `5`—not the global `10`.

Our substitution-based interpreter handles this, but the approach has limits. As programs grow more complex—with nested functions, recursive calls, and variables that shadow other variables—textual substitution becomes error-prone and inefficient.

We need a better model.

---

## 2.2 What Is an Environment?

An environment is a mapping from names to values. You can think of it as a dictionary, but with an important addition: a link to an *enclosing* environment.

```
┌─────────────────────────┐
│     Environment         │
├─────────────────────────┤
│  bindings: {            │
│    "x" → 5              │
│    "y" → 10             │
│  }                      │
│                         │
│  enclosing: ──────────────────► (parent environment)
└─────────────────────────┘
```

When we look up a name, we first check the current environment. If the name isn't there, we follow the `enclosing` link and check the parent. We keep going until we find the name or run out of environments.

This creates a *chain* of environments:

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Local     │    │  Enclosing  │    │   Global    │
│  "x" → 5    │───►│  "y" → 10   │───►│  "+" → fn   │───► None
└─────────────┘    └─────────────┘    │  "-" → fn   │
                                      │  "*" → fn   │
                                      └─────────────┘
```

Looking up `"x"` finds it immediately. Looking up `"y"` requires one hop. Looking up `"+"` requires two hops. Looking up `"undefined"` traverses the entire chain and fails.

---

## 2.3 The Environment Class

Let's build this in Python:

```python
class Environment:
    def __init__(self, bindings=None, enclosing=None):
        self.bindings = bindings or {}
        self.enclosing = enclosing

    def define(self, symbol, value):
        """Add a binding to this environment."""
        self.bindings[symbol] = value

    def get(self, symbol):
        """Look up a symbol, checking enclosing scopes if needed."""
        if symbol in self.bindings:
            return self.bindings[symbol]
        elif self.enclosing is not None:
            return self.enclosing.get(symbol)
        else:
            raise UndefinedSymbolError(f"Undefined symbol: '{symbol}'")
```

Three methods, twenty lines. That's all an environment is.

The `get` method is the heart. Watch how it searches:

```python
>>> global_env = Environment({"+": add_fn, "-": sub_fn})
>>> local_env = Environment({"x": 5}, enclosing=global_env)

>>> local_env.get("x")    # Found locally
5

>>> local_env.get("+")    # Not local, check parent → found
<function add_fn>

>>> local_env.get("z")    # Not local, not in parent → error
UndefinedSymbolError: Undefined symbol: 'z'
```

The lookup is recursive: if we don't have it, ask our parent. If they don't have it, they ask their parent. Eventually someone has it, or we hit `None` and raise an error.

---

## 2.4 Integrating Environments

Now we need to thread the environment through our evaluator. Instead of using a global `definitions` dictionary, we'll pass an environment to each call:

```python
def evaluate(expression, env):
    # Numbers evaluate to themselves
    if isinstance(expression, int):
        return expression

    # Symbols are looked up in the environment
    elif isinstance(expression, str):
        return env.get(expression)

    elif isinstance(expression, tuple):
        # ... handle special forms and applications
```

The `define` special form now adds to the current environment:

```python
if expression[0] == "define":
    name = expression[1]
    value = evaluate(expression[2], env)
    env.define(name, value)
    return None
```

And procedure application evaluates in the current environment:

```python
proc = evaluate(expression[0], env)
args = [evaluate(e, env) for e in expression[1:]]
return proc(*args)
```

The key insight: **the environment flows through the entire evaluation**. Every recursive call to `evaluate` passes the environment down. Names are always looked up relative to the current context.

---

## 2.5 Creating the Global Environment

Every program starts with a global environment containing the built-in operations:

```python
def create_global_environment():
    return Environment({
        "+": lambda x, y: x + y,
        "-": lambda x, y: x - y,
        "*": lambda x, y: x * y,
        "/": lambda x, y: x / y,
        "=": lambda x, y: x == y,
        "<": lambda x, y: x < y,
        ">": lambda x, y: x > y,
    })

global_env = create_global_environment()
```

When a user calls `evaluate(expression)` without specifying an environment, we use this global:

```python
def evaluate(expression, env=None):
    if env is None:
        env = global_env
    # ...
```

User-defined variables get added to this global environment:

```python
>>> evaluate(("define", "x", 42))
>>> evaluate("x")
42
>>> global_env.get("x")
42
```

The `x` lives alongside `+` and `*` in the same environment. But this is about to change—when we introduce functions, we'll need to create *new* environments.

---

## 2.6 The Birth of Local Scope

Consider calling a function:

```scheme
(define square (lambda (x) (* x x)))
(square 5)
```

When we call `(square 5)`, the parameter `x` should be `5`. But only inside the function body. We don't want to clobber any global `x` that might exist.

The solution: create a **new environment** for each function call.

```
Before calling (square 5):

┌──────────────────────┐
│      Global          │
│  "square" → <proc>   │
│  "+"      → <add>    │
│  "*"      → <mult>   │
└──────────────────────┘

During evaluation of (* x x):

┌──────────────────────┐
│      Local           │
│  "x" → 5             │
└─────────┬────────────┘
          │ enclosing
          ▼
┌──────────────────────┐
│      Global          │
│  "square" → <proc>   │
│  "+"      → <add>    │
│  "*"      → <mult>   │
└──────────────────────┘
```

Inside the function, `x` resolves to `5` (found locally). But `*` isn't local, so we follow the chain to global and find the multiply function.

After the function returns, the local environment disappears. The global `x` (if any) is untouched.

---

## 2.7 Building Local Environments

When a procedure is called, we:

1. Create a new environment
2. Bind each parameter to its argument
3. Set the enclosing environment
4. Evaluate the body in this new environment

Here's how that looks in code:

```python
def make_procedure(params, body, defining_env):
    """Create a procedure that remembers its defining environment."""

    def procedure(*arguments):
        # Create local environment with parameters bound to arguments
        local_env = Environment(
            bindings=dict(zip(params, arguments)),
            enclosing=defining_env
        )
        # Evaluate body in local environment
        return evaluate(body, local_env)

    return procedure
```

Notice `defining_env`. The procedure remembers the environment where it was *defined*, not where it's *called*. This distinction will become crucial in Chapter 3 when we discuss closures.

---

## 2.8 Tracing Through an Example

Let's trace `(square 5)` step by step:

```
1. evaluate(("square", 5), global_env)
   │
   ├─► proc = evaluate("square", global_env)
   │        = global_env.get("square")
   │        = <procedure>
   │
   ├─► args = [evaluate(5, global_env)]
   │        = [5]
   │
   └─► proc(5)
       │
       │  Inside the procedure:
       │
       ├─► local_env = Environment({"x": 5}, enclosing=global_env)
       │
       └─► evaluate(("*", "x", "x"), local_env)
           │
           ├─► proc = evaluate("*", local_env)
           │        = local_env.get("*")
           │        = (not in local) → global_env.get("*")
           │        = <multiply>
           │
           ├─► args = [evaluate("x", local_env), evaluate("x", local_env)]
           │        = [local_env.get("x"), local_env.get("x")]
           │        = [5, 5]
           │
           └─► multiply(5, 5) = 25
```

The local environment exists only during the call. It's created when we enter the function and forgotten when we leave.

---

## 2.9 Shadowing

What if a local variable has the same name as a global one?

```scheme
(define x 100)
(define f (lambda (x) (+ x 1)))
(f 5)    ; → 6, not 101
```

During the call to `f`:

```
┌──────────────────────┐
│      Local           │
│  "x" → 5             │◄─── lookup starts here
└─────────┬────────────┘
          │ enclosing
          ▼
┌──────────────────────┐
│      Global          │
│  "x" → 100           │     (never reached for "x")
│  "f" → <proc>        │
│  "+" → <add>         │
└──────────────────────┘
```

When we look up `"x"` in the local environment, we find it immediately. We never check the global environment. The local `x` *shadows* the global `x`.

This is the behavior programmers expect. A function's parameters are its own—they don't interfere with the outside world.

---

## 2.10 Nested Functions

Things get interesting when functions contain other functions:

```scheme
(define make-adder
  (lambda (n)
    (lambda (x) (+ x n))))

(define add5 (make-adder 5))
(add5 3)    ; → 8
```

Let's trace this:

**Step 1: Define `make-adder`**

```
┌──────────────────────────┐
│         Global           │
│  "make-adder" → <proc>   │
│  "+"          → <add>    │
└──────────────────────────┘
```

**Step 2: Call `(make-adder 5)`**

A local environment is created with `n` bound to `5`:

```
┌────────────────┐
│     Local      │
│  "n" → 5       │
└───────┬────────┘
        │ enclosing
        ▼
┌──────────────────────────┐
│         Global           │
│  "make-adder" → <proc>   │
│  "+"          → <add>    │
└──────────────────────────┘
```

Inside this environment, we evaluate `(lambda (x) (+ x n))`. This creates a new procedure—and here's the key—**that procedure captures the current environment**.

**Step 3: The returned procedure**

The inner lambda becomes a procedure that remembers where it was born:

```
<procedure add5>
  params: ("x",)
  body: ("+", "x", "n")
  defining_env: ──────────┐
                          ▼
                ┌────────────────┐
                │     Local      │
                │  "n" → 5       │
                └───────┬────────┘
                        │
                        ▼
                ┌──────────────────────────┐
                │         Global           │
                └──────────────────────────┘
```

**Step 4: Call `(add5 3)`**

Now we call the inner function with argument `3`:

```
┌────────────────┐
│  Innermost     │
│  "x" → 3       │
└───────┬────────┘
        │ enclosing
        ▼
┌────────────────┐
│     Local      │
│  "n" → 5       │
└───────┬────────┘
        │ enclosing
        ▼
┌──────────────────────────┐
│         Global           │
│  "+"          → <add>    │
└──────────────────────────┘
```

When we evaluate `(+ x n)`:
- `x` is found in the innermost environment: `3`
- `n` is found one level up: `5`
- `+` is found in global: `<add>`
- Result: `3 + 5 = 8`

The chain of environments preserves the value of `n` from when `add5` was created.

---

## 2.11 The Environment Diagram

This pattern is so common that it has a name: the **environment diagram**. It's a visual tool for understanding how names resolve.

Here's the full diagram for our `make-adder` example after `add5` is called:

```
              GLOBAL ENVIRONMENT
              ┌────────────────────────────────────────────┐
              │  "make-adder" ────────────────┐            │
              │  "add5" ──────────────────────┼──┐         │
              │  "+" → <add>                  │  │         │
              │  "-" → <sub>                  │  │         │
              │  "*" → <mult>                 │  │         │
              └────────────────────────────────┼──┼─────────┘
                             ▲                 │  │
                             │                 │  │
                ┌────────────┴──────┐          │  │
                │ <make-adder proc> │◄─────────┘  │
                │   params: (n)     │             │
                │   body: (lambda   │             │
                │         (x)       │             │
                │         (+ x n))  │             │
                └───────────────────┘             │
                                                  │
              ┌───────────────────────────────────┘
              │
              │    ENVIRONMENT E1 (from calling make-adder)
              │    ┌──────────────────┐
              │    │  "n" → 5         │
              │    └────────┬─────────┘
              │             │ enclosing → GLOBAL
              │             │
              │    ┌────────┴──────────┐
              └───►│ <add5 proc>       │
                   │   params: (x)     │
                   │   body: (+ x n)   │
                   │   env: E1         │
                   └───────────────────┘
```

Each procedure points to the environment where it was defined. When called, it extends *that* environment, not the current one.

---

## 2.12 Lexical vs. Dynamic Scope

Our environment model implements **lexical scoping** (also called static scoping). A function's free variables are looked up in the environment where the function was *defined*.

The alternative is **dynamic scoping**, where free variables are looked up in the environment where the function is *called*.

Consider:

```scheme
(define x 10)
(define f (lambda () x))
(define g (lambda () (define x 20) (f)))
(g)    ; Lexical: 10, Dynamic: 20
```

With lexical scoping (our model), `f` was defined in the global environment, so it sees the global `x` (10).

With dynamic scoping, `f` is *called* from inside `g`, where `x` is 20.

Most modern languages use lexical scoping because it's easier to reason about. You can tell which variable a name refers to just by looking at the code—you don't need to trace through every possible call path.

> *"Lexical scoping... leads to more modular programs."*
> — SICP, Section 3.2

---

## 2.13 The Minimal Implementation

Let's see how our 60-line interpreter from Chapter 1 handles environments. It doesn't use an `Environment` class—instead, it uses substitution:

```python
def procedure(*arguments):
    names = expression[1]
    body = expression[2]

    for i, argument in enumerate(arguments):
        name = names[i]
        body = substitute(body, name, argument)

    return evaluate(body)
```

Rather than creating an environment with `x → 5`, it rewrites the body to replace every `x` with `5`. This achieves the same effect for simple cases.

But substitution has costs:
- It copies and rewrites expressions (slower for large programs)
- It can't handle mutable variables (Chapter 4)
- It's harder to debug (no environment to inspect)

The environment model is more explicit. It makes the name-value mapping concrete, which helps when things go wrong.

---

## 2.14 Looking Forward: Closures

We've seen that functions capture their defining environment. This has a name: **closure**.

A closure is a function plus the environment in which it was created. The function "closes over" the variables it references.

In Chapter 3, we'll explore closures deeply:
- How to implement them properly
- Why they enable powerful patterns
- The difference between substitution and environment-based closure

But the foundation is here. An environment is a chain of bindings. Functions remember their chain. That's the whole story.

---

## 2.15 The Complete Environment Implementation

Here's our full `Environment` class with error handling:

```python
class UndefinedSymbolError(Exception):
    """Raised when accessing an undefined symbol."""
    pass


class Environment:
    """
    Environment for storing variable bindings with lexical scoping.
    """

    def __init__(self, bindings=None, enclosing=None):
        self.bindings = bindings or {}
        self.enclosing = enclosing

    def define(self, symbol, value):
        """Define a new variable in this environment."""
        self.bindings[symbol] = value

    def get(self, symbol):
        """
        Look up a variable, checking enclosing scopes if needed.
        """
        if symbol in self.bindings:
            return self.bindings[symbol]
        elif self.enclosing is not None:
            return self.enclosing.get(symbol)
        else:
            raise UndefinedSymbolError(f"Undefined symbol: '{symbol}'")

    def copy(self):
        """Create a shallow copy of this environment."""
        return Environment(self.bindings.copy(), self.enclosing)
```

And the integrated evaluator:

```python
def create_global_environment():
    return Environment({
        "+": lambda x, y: x + y,
        "-": lambda x, y: x - y,
        "*": lambda x, y: x * y,
        "/": lambda x, y: x / y,
        "=": lambda x, y: x == y,
        "<": lambda x, y: x < y,
        ">": lambda x, y: x > y,
    })


global_env = create_global_environment()


def evaluate(expression, env=None):
    if env is None:
        env = global_env

    # Atoms
    if isinstance(expression, int):
        return expression

    if isinstance(expression, str):
        return env.get(expression)

    # Compound expressions
    if isinstance(expression, tuple):
        if expression[0] == "define":
            env.define(expression[1], evaluate(expression[2], env))
            return None

        if expression[0] == "if":
            if evaluate(expression[1], env):
                return evaluate(expression[2], env)
            return evaluate(expression[3], env)

        if expression[0] == "lambda":
            params = expression[1]
            body = expression[2]

            def procedure(*arguments):
                local_env = Environment(
                    dict(zip(params, arguments)),
                    env  # Capture the defining environment
                )
                return evaluate(body, local_env)

            return procedure

        # Application
        proc = evaluate(expression[0], env)
        args = [evaluate(e, env) for e in expression[1:]]
        return proc(*args)
```

The lambda case is where environments come alive. Each procedure captures `env`—the environment at definition time—and uses it as the parent when creating local environments.

---

## Exercises

**2.1** Draw the environment diagram for this program after evaluating all expressions:

```scheme
(define x 1)
(define y 2)
(define f (lambda (x) (+ x y)))
(f 10)
```

What is the result of `(f 10)`? Which `x` does the function see?

**2.2** Implement a `set!` operation that modifies an existing variable instead of creating a new one. It should search up the environment chain to find where the variable is defined. (Hint: you'll need a new method on `Environment`.)

**2.3** What happens if you call a function recursively? Draw the environment chain for:

```scheme
(define countdown
  (lambda (n)
    (if (= n 0)
        "done"
        (countdown (- n 1)))))
(countdown 3)
```

How many local environments are created?

**2.4** Add a `let` special form that creates local bindings:

```scheme
(let ((x 5) (y 10)) (+ x y))    ; → 15
```

This is syntactic sugar for an immediately-called lambda.

**2.5** Our `get` method is recursive. Rewrite it as an iterative loop. Which version do you prefer?

---

## Summary

- An **environment** is a mapping from names to values, plus a link to an enclosing environment.
- Name lookup searches the current environment, then walks up the chain.
- Each function call creates a **new local environment** with parameters bound to arguments.
- Local variables **shadow** outer variables with the same name.
- Functions capture their **defining environment**, enabling **lexical scoping**.
- The environment model replaces textual substitution with explicit data structures.

In the next chapter, we'll explore lambda in depth. We'll see how closures enable powerful patterns—from private state to currying to the foundations of object-oriented programming. The environment is the stage; functions are the actors.
