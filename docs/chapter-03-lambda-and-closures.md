# Chapter 3: Lambda + Closures

> *"It is better to have 100 functions operate on one data structure than 10 functions on 10 data structures."*
> — Alan Perlis

In Chapters 1 and 2, we built an interpreter that evaluates expressions and manages names. But we haven't yet explored the feature that makes Scheme—and functional programming—truly powerful.

**Lambda.**

The word comes from Alonzo Church's lambda calculus, a formal system from the 1930s that predates computers. Church used the Greek letter λ to denote functions. Scheme inherited the word, and it spread to Python, JavaScript, Ruby, and beyond.

In this chapter, we'll understand lambda deeply. We'll see how functions can be created on the fly, passed as arguments, returned as values, and bundled with private data. Along the way, we'll compare two implementation strategies—substitution and environments—and discover why closures are one of the most powerful ideas in programming.

---

## 3.1 What Is Lambda?

Lambda creates a function. That's it.

```scheme
(lambda (x) (* x x))
```

This expression creates a function that takes one argument `x` and returns `x` squared. The function has no name—it's anonymous. We can use it immediately:

```scheme
((lambda (x) (* x x)) 5)    ; → 25
```

Or we can give it a name:

```scheme
(define square (lambda (x) (* x x)))
(square 5)    ; → 25
```

The `define` doesn't make the function—`lambda` does. `define` just stores it.

In Python tuples, the lambda expression looks like:

```python
("lambda", ("x",), ("*", "x", "x"))
```

Three parts:
1. The keyword `"lambda"`
2. A tuple of parameter names: `("x",)`
3. The body expression: `("*", "x", "x")`

When evaluated, this produces a callable Python function.

---

## 3.2 Functions Are Values

Here's an idea that changed programming: **functions are data**.

A function can be:
- Stored in a variable
- Passed as an argument to another function
- Returned as the result of a function
- Stored in a data structure

This is what "first-class functions" means. Functions are values like any other—no more special than numbers or strings.

```scheme
; Store in a variable
(define f (lambda (x) (+ x 1)))

; Pass as an argument
(define apply-twice (lambda (f x) (f (f x))))
(apply-twice f 5)    ; → 7

; Return from a function
(define make-adder (lambda (n) (lambda (x) (+ x n))))
(define add10 (make-adder 10))
(add10 5)    ; → 15
```

That last example is worth pausing on. `make-adder` is a function that *returns a function*. When we call `(make-adder 10)`, we get back a new function—one that adds 10 to its argument.

This is not exotic. It's the foundation of modular, composable code.

---

## 3.3 Implementing Lambda: The Substitution Approach

How does our interpreter handle lambda? Let's look at the simple approach from Chapter 1:

```python
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
```

When we evaluate a lambda expression, we return a Python function (`procedure`). When that function is called:

1. Get the parameter names and body from the original expression
2. For each argument, substitute its value into the body
3. Evaluate the rewritten body

Let's trace `((lambda (x) (* x x)) 5)`:

```
1. evaluate(("lambda", ("x",), ("*", "x", "x")))
   → Returns <procedure>

2. evaluate((procedure, 5))
   → proc = <procedure>
   → args = [5]
   → proc(5)

3. Inside procedure(5):
   → names = ("x",)
   → body = ("*", "x", "x")
   → Substitute "x" with 5:
     body = substitute(("*", "x", "x"), "x", 5)
          = ("*", 5, 5)
   → evaluate(("*", 5, 5))
   → 25
```

The substitution physically rewrites the expression tree before evaluating it:

```
Before substitution:        After substitution:

      *                           *
     / \                         / \
    x   x                       5   5
```

This is conceptually simple. It matches how you might evaluate functions by hand—replace the variables with their values, then compute.

---

## 3.4 The Substitute Function

Let's examine `substitute` more closely:

```python
def substitute(expr, name, value):
    if expr == name:
        return value
    elif isinstance(expr, tuple):
        return tuple([substitute(term, name, value) for term in expr])
    return expr
```

Three cases:
1. If `expr` is the name we're substituting, return the value
2. If `expr` is a tuple, recursively substitute in each element
3. Otherwise (numbers, other symbols), return unchanged

This walks the entire expression tree, replacing every occurrence of `name` with `value`.

```python
>>> substitute(("*", "x", "x"), "x", 5)
("*", 5, 5)

>>> substitute(("+", "x", ("*", "x", "y")), "x", 3)
("+", 3, ("*", 3, "y"))
```

For multiple parameters, we substitute one at a time:

```python
def procedure(*arguments):
    names = expression[1]
    body = expression[2]

    for i, argument in enumerate(arguments):
        name = names[i]
        body = substitute(body, name, argument)

    return evaluate(body)
```

Each substitution transforms the body, and the final result is evaluated.

---

## 3.5 Implementing Lambda: The Environment Approach

The substitution approach works, but it has a cost: we copy and rewrite expressions on every function call. For large programs with deep recursion, this adds overhead.

The environment approach avoids rewriting. Instead of substituting values into the expression, we store them in an environment and look them up during evaluation.

```python
elif expression[0] == "lambda":
    params = expression[1]
    body = expression[2]

    def procedure(*arguments):
        # Create new environment with parameters bound to arguments
        local_env = Environment(
            dict(zip(params, arguments)),
            env  # Capture the defining environment
        )
        return evaluate(body, local_env)

    return procedure
```

When the procedure is called:
1. Create a new environment
2. Bind each parameter to its corresponding argument
3. Set the enclosing environment to where the lambda was defined
4. Evaluate the body in this new environment

Let's trace the same example:

```
1. evaluate(("lambda", ("x",), ("*", "x", "x")), global_env)
   → Returns <procedure> that captures global_env

2. evaluate((procedure, 5), global_env)
   → proc = <procedure>
   → args = [5]
   → proc(5)

3. Inside procedure(5):
   → local_env = Environment({"x": 5}, enclosing=global_env)
   → evaluate(("*", "x", "x"), local_env)

4. evaluate(("*", "x", "x"), local_env)
   → proc = local_env.get("*") → (not local) → global_env.get("*") → <mult>
   → args = [local_env.get("x"), local_env.get("x")] = [5, 5]
   → mult(5, 5) → 25
```

The expression tree is never modified. Instead, we create environments and look up values as we go.

---

## 3.6 What Is a Closure?

Notice something subtle in the environment approach:

```python
def procedure(*arguments):
    local_env = Environment(
        dict(zip(params, arguments)),
        env  # ← This is captured from when lambda was DEFINED
    )
    return evaluate(body, local_env)
```

The procedure remembers `env`—the environment that existed when the lambda was evaluated. This is called **closing over** the environment.

A **closure** is a function bundled with its defining environment.

Why does this matter? Consider:

```scheme
(define make-adder
  (lambda (n)
    (lambda (x) (+ x n))))

(define add5 (make-adder 5))
(add5 3)    ; → 8
```

When `(make-adder 5)` runs:
1. We enter `make-adder` with `n = 5`
2. We evaluate `(lambda (x) (+ x n))`
3. This creates a closure that captures the current environment (where `n = 5`)
4. We return this closure

Later, when `(add5 3)` runs:
1. We call the closure with `x = 3`
2. We create a local environment: `{"x": 3}` extending the captured environment
3. We evaluate `(+ x n)`
4. `x` is found locally: `3`
5. `n` is found in the captured environment: `5`
6. Result: `8`

The closure "remembers" that `n` was `5`, even though `make-adder` has long since returned.

```
┌──────────────────────────────────────────────┐
│  <add5 closure>                              │
│                                              │
│  params: ("x",)                              │
│  body:   ("+", "x", "n")                     │
│  env: ──────────────────────────┐            │
│                                 │            │
└─────────────────────────────────┼────────────┘
                                  │
                                  ▼
                      ┌───────────────────────┐
                      │  Environment E1       │
                      │    "n" → 5            │
                      └───────────┬───────────┘
                                  │ enclosing
                                  ▼
                      ┌───────────────────────┐
                      │  Global Environment   │
                      │    "+" → <add>        │
                      │    "make-adder" → ... │
                      └───────────────────────┘
```

---

## 3.7 Closures in the Substitution Model

Interestingly, our simple substitution-based interpreter also handles closures correctly. How?

When `make-adder` creates the inner lambda:

```python
("lambda", ("x",), ("+", "x", "n"))
```

Before returning, it substitutes `n` with `5`:

```python
("lambda", ("x",), ("+", "x", 5))
```

The returned lambda has `5` baked into its body. There's no reference to `n` anymore—the substitution happened at creation time.

This achieves the same result through a different mechanism. The environment approach stores values in a data structure; the substitution approach rewrites the code.

Both are valid. Both implement closures. The difference is in efficiency and debuggability.

---

## 3.8 Higher-Order Functions

A **higher-order function** is a function that takes functions as arguments or returns functions as results. We've already seen `make-adder`. Here are more examples:

**Apply a function twice:**

```scheme
(define apply-twice
  (lambda (f x)
    (f (f x))))

(define increment (lambda (x) (+ x 1)))
(apply-twice increment 5)    ; → 7
```

In our interpreter:

```python
>>> apply_twice = evaluate(("lambda", ("f", "x"), ("f", ("f", "x"))))
>>> increment = evaluate(("lambda", ("x",), ("+", "x", 1)))
>>> apply_twice(increment, 5)
7
```

**Compose two functions:**

```scheme
(define compose
  (lambda (f g)
    (lambda (x) (f (g x)))))

(define double (lambda (x) (* x 2)))
(define square (lambda (x) (* x x)))

(define double-then-square (compose square double))
(double-then-square 3)    ; → 36  (3*2=6, 6*6=36)
```

**Map a function over arguments:**

```scheme
; Without built-in lists, we simulate with multiple applications
(define map-3
  (lambda (f a b c)
    ; Returns three results... but we can only return one value
    ; This is where we'd need cons/car/cdr or multiple values
    (f c)))  ; Simplified
```

Higher-order functions are the bread and butter of functional programming. They let you abstract over *actions*, not just data.

---

## 3.9 Currying

**Currying** transforms a function of multiple arguments into a sequence of functions, each taking one argument.

Instead of:

```scheme
(define add (lambda (x y) (+ x y)))
(add 3 5)    ; → 8
```

We write:

```scheme
(define add
  (lambda (x)
    (lambda (y)
      (+ x y))))

((add 3) 5)    ; → 8
```

The curried `add` takes one argument and returns a function that takes the next argument. We call it with two separate applications.

Why bother? Partial application. We can "fill in" arguments one at a time:

```scheme
(define add3 (add 3))
(add3 5)    ; → 8
(add3 10)   ; → 13
```

This works because `(add 3)` returns a closure that remembers `x = 3`. Each closure is a specialized version of the original function.

Currying is the natural style in lambda calculus, where all functions take exactly one argument. Multi-argument functions are syntactic sugar for nested lambdas.

---

## 3.10 Private State Without Objects

Closures can encapsulate state, providing privacy without classes or objects.

```scheme
(define make-counter
  (lambda (initial)
    (lambda ()
      ; We need set! to mutate, which we'll cover in Chapter 4
      ; For now, imagine this returns and increments
      initial)))
```

A more realistic example using our current features:

```scheme
(define make-account
  (lambda (balance)
    (lambda (amount)
      ; Returns new balance after withdrawal
      (- balance amount))))

(define my-account (make-account 100))
(my-account 30)    ; → 70
```

The `balance` is private. No code outside `make-account` can access it directly. The only way to interact is through the returned function.

This is the essence of **encapsulation**—one of the pillars of object-oriented programming—achieved with just lambda and closure. No `class` keyword needed.

---

## 3.11 Functions Returning Functions

Let's trace through a complete example of functions returning functions:

```scheme
(define make-multiplier
  (lambda (factor)
    (lambda (x) (* factor x))))

(define double (make-multiplier 2))
(define triple (make-multiplier 3))

(double 5)    ; → 10
(triple 5)    ; → 15
```

**Step 1: Define `make-multiplier`**

```
Global Environment:
┌────────────────────────────────────┐
│ "make-multiplier" → <procedure>    │
│ "*" → <mult>                       │
└────────────────────────────────────┘
```

**Step 2: Call `(make-multiplier 2)`**

```
Call Environment E1:
┌────────────────────┐
│ "factor" → 2       │
└─────────┬──────────┘
          │ enclosing
          ▼
┌────────────────────────────────────┐
│ Global                             │
└────────────────────────────────────┘

Creates closure:
┌─────────────────────────────┐
│ params: ("x",)              │
│ body: ("*", "factor", "x")  │
│ env: E1 ────────────────────┼──► where factor=2
└─────────────────────────────┘
```

**Step 3: Define `double`**

```
Global Environment:
┌────────────────────────────────────┐
│ "make-multiplier" → <procedure>    │
│ "double" → <closure with E1>       │
│ "*" → <mult>                       │
└────────────────────────────────────┘
```

**Step 4: Call `(make-multiplier 3)`**

This creates a *different* environment E2:

```
Call Environment E2:
┌────────────────────┐
│ "factor" → 3       │
└─────────┬──────────┘
          │ enclosing
          ▼
┌────────────────────────────────────┐
│ Global                             │
└────────────────────────────────────┘

Creates closure:
┌─────────────────────────────┐
│ params: ("x",)              │
│ body: ("*", "factor", "x")  │
│ env: E2 ────────────────────┼──► where factor=3
└─────────────────────────────┘
```

**Step 5: Call `(double 5)`**

```
Call Environment E3:
┌────────────────────┐
│ "x" → 5            │
└─────────┬──────────┘
          │ enclosing
          ▼
┌────────────────────┐
│ E1: "factor" → 2   │
└─────────┬──────────┘
          │ enclosing
          ▼
┌────────────────────────────────────┐
│ Global: "*" → <mult>               │
└────────────────────────────────────┘

Evaluate ("*", "factor", "x"):
  - "*" found in Global: <mult>
  - "factor" found in E1: 2
  - "x" found in E3: 5
  - Result: 2 * 5 = 10
```

`double` and `triple` are independent closures. Each captured its own `factor` value when it was created.

---

## 3.12 Comparing the Two Approaches

Let's put our two implementation strategies side by side:

| Aspect | Substitution | Environment |
|--------|--------------|-------------|
| **Mechanism** | Rewrite expression tree | Store values in data structure |
| **When values are bound** | At call time, before evaluation | At call time, during evaluation |
| **Memory** | Copies expressions | Shares expression, creates environments |
| **Speed** | Slower for large expressions | Faster (no tree rewriting) |
| **Debugging** | Hard (code changes) | Easier (environments inspectable) |
| **Closures** | Values baked into code | References to captured environment |

**When substitution wins:**

- Simpler to understand
- No environment data structure needed
- Good for teaching and small programs

**When environments win:**

- Scales to large programs
- Supports debugging and introspection
- Required for mutable state (Chapter 4)
- Standard approach in real interpreters

Both achieve correct semantics for pure functional code. The choice is engineering, not mathematics.

---

## 3.13 The Lambda Calculus Connection

Our implementation embodies ideas from Alonzo Church's **lambda calculus** (1930s). In that system:

- Everything is a function
- Functions take exactly one argument
- Multi-argument functions use currying
- There are no numbers, booleans, or data structures—just functions

Remarkably, this is enough to compute anything computable. Numbers, booleans, pairs, lists—all can be encoded as functions. We'll explore this in Chapter 5.

For now, notice that our interpreter already supports the core lambda calculus:

```scheme
; Identity function
(lambda (x) x)

; Apply a function to an argument
((lambda (f) (lambda (x) (f x))) ...)

; Self-application (used in recursion)
((lambda (x) (x x)) (lambda (x) (x x)))
```

The last example is infinite recursion—it never terminates. Lambda calculus can express non-termination, just like real programs.

---

## 3.14 Recursion and Lambda

How does recursion work with lambda? Consider the Fibonacci function:

```scheme
(define fibonacci
  (lambda (n)
    (if (< n 2)
        1
        (+ (fibonacci (- n 2)) (fibonacci (- n 1))))))
```

Inside the body, we call `fibonacci`. But when the lambda is created, `fibonacci` isn't defined yet—we're in the middle of defining it!

This works because:
1. We create the procedure (capturing the current environment)
2. We bind `fibonacci` to this procedure in the global environment
3. When the procedure runs, it looks up `fibonacci` and finds itself

The lookup happens at *call time*, not *definition time*. By then, `fibonacci` exists.

```
Timeline:
─────────────────────────────────────────────────────────────────►
    │                    │                    │
    │ Create procedure   │ Bind name          │ Call procedure
    │ (body references   │ "fibonacci" →      │ looks up
    │  "fibonacci")      │ <procedure>        │ "fibonacci"
    │                    │                    │ and finds it
```

This is why recursive functions "just work" in most languages—name resolution is deferred until execution.

---

## 3.15 Anonymous Recursion

But what if we want recursion without naming the function? This is possible using the **Y combinator**:

```scheme
(define Y
  (lambda (f)
    ((lambda (x) (f (lambda (y) ((x x) y))))
     (lambda (x) (f (lambda (y) ((x x) y)))))))
```

The Y combinator is a fixed-point combinator—it lets a function call itself without having a name. We'll explore this in Chapter 5.

For now, appreciate that lambda is powerful enough to express recursion even without `define`.

---

## 3.16 The Complete Lambda Implementation

Here's our environment-based lambda, with full context:

```python
class Environment:
    def __init__(self, bindings=None, enclosing=None):
        self.bindings = bindings or {}
        self.enclosing = enclosing

    def define(self, symbol, value):
        self.bindings[symbol] = value

    def get(self, symbol):
        if symbol in self.bindings:
            return self.bindings[symbol]
        elif self.enclosing is not None:
            return self.enclosing.get(symbol)
        else:
            raise UndefinedSymbolError(f"Undefined symbol: '{symbol}'")


def evaluate(expression, env=None):
    if env is None:
        env = global_env

    # Atoms
    if isinstance(expression, (int, float)):
        return expression

    if isinstance(expression, str):
        return env.get(expression)

    if callable(expression):
        return expression

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
                if len(arguments) != len(params):
                    raise ArityError(
                        f"Expected {len(params)} arguments, got {len(arguments)}"
                    )
                local_env = Environment(
                    dict(zip(params, arguments)),
                    env  # Closure: capture the defining environment
                )
                return evaluate(body, local_env)

            return procedure

        # Application
        proc = evaluate(expression[0], env)
        args = [evaluate(e, env) for e in expression[1:]]
        return proc(*args)
```

The key line is:

```python
env  # Closure: capture the defining environment
```

That single reference to `env` is what makes closures work. The procedure carries its birthplace with it forever.

---

## 3.17 Testing Our Lambda

Let's verify our implementation handles the key cases:

```python
# Simple lambda
>>> square = evaluate(("lambda", ("x",), ("*", "x", "x")))
>>> square(5)
25

# Closure capturing a variable
>>> env = create_global_environment()
>>> evaluate(("define", "n", 10), env)
>>> add_n = evaluate(("lambda", ("x",), ("+", "x", "n")), env)
>>> add_n(5)
15

# Higher-order function
>>> apply_twice = evaluate(
...     ("lambda", ("f", "x"), ("f", ("f", "x")))
... )
>>> inc = evaluate(("lambda", ("x",), ("+", "x", 1)))
>>> apply_twice(inc, 5)
7

# Function returning function
>>> make_adder = evaluate(
...     ("lambda", ("n",), ("lambda", ("x",), ("+", "x", "n")))
... )
>>> add5 = make_adder(5)
>>> add5(3)
8
>>> add10 = make_adder(10)
>>> add10(3)
13

# Recursion
>>> env = create_global_environment()
>>> fib = ("lambda", ("n",),
...     ("if", ("<", "n", 2),
...         1,
...         ("+", ("fib", ("-", "n", 1)), ("fib", ("-", "n", 2)))))
>>> evaluate(("define", "fib", fib), env)
>>> evaluate(("fib", 10), env)
89
```

All the patterns work. Lambda is complete.

---

## Exercises

**3.1** Trace the evaluation of `((lambda (x y) (+ (* x x) (* y y))) 3 4)` step by step, showing each substitution (for the substitution approach) or each environment created (for the environment approach).

**3.2** Implement a `thrice` function that applies a function three times:

```scheme
(define thrice (lambda (f) (lambda (x) (f (f (f x))))))
(define inc (lambda (x) (+ x 1)))
((thrice inc) 0)    ; → 3
```

Verify it works in the interpreter.

**3.3** Write a `flip` function that reverses the order of arguments to a two-argument function:

```scheme
(define flip (lambda (f) (lambda (x y) (f y x))))
(define sub (lambda (a b) (- a b)))
((flip sub) 3 10)    ; → 7 (computes 10 - 3, not 3 - 10)
```

**3.4** The environment approach captures the defining environment by reference. What happens if we modify a variable in the enclosing scope after creating a closure? Test this:

```scheme
(define n 5)
(define f (lambda () n))
(f)              ; → ?
(define n 10)
(f)              ; → ?
```

Does the closure see the old value or the new value?

**3.5** Rewrite the substitution-based lambda to be more efficient by only substituting when the name actually appears in the body. (Hint: first check if `name in str(body)` or write a `contains` function.)

---

## Summary

- **Lambda** creates anonymous functions with parameters and a body
- Functions are **first-class values**: stored, passed, and returned
- **Substitution** replaces parameters with arguments in the expression tree
- **Environment-based closures** store values in linked dictionaries
- A **closure** is a function plus its defining environment
- **Higher-order functions** take or return functions
- **Currying** transforms multi-argument functions into chains of single-argument functions
- Closures enable **private state** without classes
- Both implementation strategies are valid; environments scale better
- **Recursion** works because name lookup is deferred until call time

In the next chapter, we'll confront a question we've been avoiding: what happens when values change? The substitution model will break down, and we'll need environments not just for efficiency, but for correctness. Welcome to state.
