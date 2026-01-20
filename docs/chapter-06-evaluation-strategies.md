# Chapter 6: Evaluation Strategies

> *"Major parts of the book are devoted to setting up competing approaches to computation. Consequences and tradeoffs of these decisions are then explored. Often, the differences are subtle, but insightful."*
> — David Beazley on SICP

When should arguments be evaluated?

This question seems trivial. Evaluate them before calling the function, obviously. That's what every language does.

Except it isn't. And the consequences of this choice ripple through language design in ways that affect what programs you can write, how efficient they are, and whether they terminate at all.

In this chapter, we'll explore **evaluation strategies**—the rules that determine when expressions are evaluated. We'll discover why `if` must be a special form, how lazy evaluation enables infinite data structures, and why tail calls matter for recursive programs.

---

## 6.1 Applicative Order: Evaluate Arguments First

Our interpreter uses **applicative order evaluation** (also called **eager evaluation** or **call-by-value**). The rule is simple:

> Evaluate all arguments before applying the function.

Consider:

```scheme
(define (square x) (* x x))

(square (+ 1 2))
```

The evaluation proceeds:

```
(square (+ 1 2))
    │
    │  First, evaluate the argument (+ 1 2)
    ▼
(square 3)
    │
    │  Then apply square to 3
    ▼
(* 3 3)
    │
    ▼
   9
```

The argument `(+ 1 2)` is evaluated to `3` before `square` is called. Inside `square`, `x` is already `3`—the addition has been completed.

This is how most programming languages work: Python, JavaScript, Java, C, Ruby, Go. It's intuitive because it matches how we think about function calls in mathematics.

---

## 6.2 Normal Order: Evaluate When Needed

There's an alternative: **normal order evaluation** (also called **lazy evaluation** or **call-by-need**). The rule:

> Don't evaluate arguments until their values are actually needed.

The same example:

```scheme
(square (+ 1 2))
```

Under normal order:

```
(square (+ 1 2))
    │
    │  Substitute (+ 1 2) for x in the body, without evaluating
    ▼
(* (+ 1 2) (+ 1 2))
    │
    │  Now we need the values for multiplication
    ▼
(* 3 (+ 1 2))
    │
    ▼
(* 3 3)
    │
    ▼
   9
```

The argument `(+ 1 2)` is passed unevaluated. It only gets computed when `*` actually needs the numbers.

Notice that `(+ 1 2)` appears twice in the expanded form and might be computed twice. Practical lazy languages like Haskell avoid this by **memoizing**—computing once and caching the result.

---

## 6.3 Same Result, Different Path

For pure computations, both strategies give the same answer:

```
APPLICATIVE ORDER                NORMAL ORDER

(square (+ 1 2))                 (square (+ 1 2))
        │                                │
        ▼                                ▼
(square 3)                       (* (+ 1 2) (+ 1 2))
        │                                │
        ▼                                ▼
(* 3 3)                          (* 3 (+ 1 2))
        │                                │
        ▼                                ▼
   9                             (* 3 3)
                                         │
                                         ▼
                                    9
```

Both arrive at `9`. Applicative order does less work (one addition instead of two). But for this example, the final result is identical.

So why does it matter?

---

## 6.4 When Evaluation Order Changes Everything

Consider this program:

```scheme
(define (p) (p))

(define (test x y)
  (if (= x 0) 0 y))

(test 0 (p))
```

The function `(p)` calls itself infinitely—it never returns.

**Under applicative order:**

```
(test 0 (p))
    │
    │  Evaluate arguments first
    │  Evaluate 0 → 0
    │  Evaluate (p) → ... infinite loop!
    ▼
   ∞ (never terminates)
```

We try to evaluate `(p)` before calling `test`. Since `(p)` never terminates, the program hangs.

**Under normal order:**

```
(test 0 (p))
    │
    │  Substitute without evaluating
    ▼
(if (= 0 0) 0 (p))
    │
    │  Evaluate condition: (= 0 0) → true
    │  Since true, return the "then" branch
    ▼
   0
```

The argument `(p)` is never evaluated because it's in the "else" branch, which isn't needed.

**The same program terminates under normal order but loops forever under applicative order.**

---

## 6.5 Why `if` Must Be Special

This explains why `if` is a **special form** in our interpreter, not an ordinary function.

If `if` were an ordinary function:

```scheme
(define (my-if condition then-branch else-branch)
  (if condition then-branch else-branch))

(my-if (= 1 1) 2 (/ 1 0))
```

Under applicative order, all arguments are evaluated first:
- `(= 1 1)` → `true`
- `2` → `2`
- `(/ 1 0)` → **ERROR: division by zero**

The error happens even though we'd never use the else-branch. The program crashes before `my-if` even runs.

The built-in `if` avoids this by **not** evaluating both branches. It evaluates the condition first, then evaluates only the branch that's needed:

```python
if expression[0] == "if":
    if evaluate(expression[1], env):  # Evaluate condition
        return evaluate(expression[2], env)  # Only evaluate "then"
    return evaluate(expression[3], env)  # Only evaluate "else"
```

This is special evaluation—the normal rules don't apply.

---

## 6.6 Special Forms Revisited

Looking back at our special forms, we can now see why each one is special:

| Form | Why Special? |
|------|--------------|
| `define` | Doesn't evaluate the name (first argument) |
| `if` | Only evaluates one branch |
| `lambda` | Doesn't evaluate the body at definition time |

Compare to ordinary function application:

```python
# Ordinary application
proc = evaluate(expression[0], env)
args = [evaluate(e, env) for e in expression[1:]]  # ALL args evaluated
return proc(*args)
```

Special forms break this pattern. They have custom rules about what gets evaluated and when.

---

## 6.7 Simulating Laziness with Thunks

Even in an eager language, we can simulate lazy evaluation using **thunks**—functions that wrap delayed computations.

```scheme
; Eager version (evaluates immediately)
(define value (expensive-computation))

; Lazy version (delays until needed)
(define thunk (lambda () (expensive-computation)))

; Force evaluation when needed
(thunk)
```

A thunk is a zero-argument function. The computation is "frozen" inside the lambda. Calling the thunk "thaws" it—forces the evaluation.

We can build lazy `if` this way:

```scheme
(define (lazy-if condition then-thunk else-thunk)
  (if condition (then-thunk) (else-thunk)))

; Usage - wrap branches in lambdas
(lazy-if (= 1 1)
  (lambda () 2)
  (lambda () (/ 1 0)))  ; Never evaluated!
```

Now the branches are thunks. Only the selected branch gets forced.

---

## 6.8 Infinite Data Structures

Lazy evaluation enables something remarkable: **infinite data structures**.

Consider an infinite list of ones:

```scheme
; This would be infinite under eager evaluation - can't create it!
(define ones (cons 1 ones))

; With lazy evaluation, it's fine
(define (lazy-ones)
  (cons 1 (lambda () (lazy-ones))))
```

The structure is infinite, but we only compute as much as we need:

```scheme
(car (lazy-ones))       ; → 1
(car (cdr (lazy-ones))) ; → 1
; We can take any finite prefix without computing the whole thing
```

Or the natural numbers:

```scheme
(define (naturals-from n)
  (cons n (lambda () (naturals-from (+ n 1)))))

(define naturals (naturals-from 0))

; (0, <thunk>)
; where <thunk>, when forced, gives (1, <thunk>)
; where that <thunk>, when forced, gives (2, <thunk>)
; ... forever
```

Haskell's default laziness makes this natural:

```haskell
ones = 1 : ones           -- Infinite list of ones
naturals = [0..]          -- 0, 1, 2, 3, ...
fibs = 0 : 1 : zipWith (+) fibs (tail fibs)  -- Fibonacci sequence
```

You can't do this in eager languages without explicit thunks.

---

## 6.9 Trade-offs

Neither strategy is universally better:

| Aspect | Applicative (Eager) | Normal (Lazy) |
|--------|---------------------|---------------|
| **Simplicity** | Easier to understand | More complex |
| **Debugging** | Predictable evaluation order | Order can surprise |
| **Efficiency** | No redundant evaluation | May recompute (unless memoized) |
| **Space** | Immediate cleanup | Thunks accumulate |
| **Termination** | May loop unnecessarily | May terminate when eager loops |
| **Infinite data** | Requires explicit thunks | Natural |
| **Side effects** | Predictable timing | Unpredictable timing |

The last point is crucial. With side effects, evaluation order matters:

```scheme
(define (print-and-return x)
  (display x)
  x)

(+ (print-and-return 1) (print-and-return 2))
```

With applicative order, you'll see `12` (or `21`—order among arguments may vary).
With normal order, you might see nothing until the values are needed, or see them in a different order.

This is why lazy languages like Haskell tend to be pure functional—side effects and laziness don't mix well.

---

## 6.10 Recursion vs. Iteration

Evaluation strategies also interact with how we write loops.

Scheme doesn't have `for` or `while`. Instead, we use recursion:

```scheme
(define (factorial n)
  (if (= n 1)
      1
      (* n (factorial (- n 1)))))
```

Let's trace `(factorial 4)`:

```
(factorial 4)
(* 4 (factorial 3))
(* 4 (* 3 (factorial 2)))
(* 4 (* 3 (* 2 (factorial 1))))
(* 4 (* 3 (* 2 1)))
(* 4 (* 3 2))
(* 4 6)
24
```

See the shape? It **expands** as we go down, then **contracts** as we multiply. Each recursive call adds a pending operation to the stack.

For `(factorial 1000)`, we'd have 999 pending multiplications—999 stack frames.

---

## 6.11 Tail Recursion

There's a better way. We can rewrite factorial to be **tail recursive**:

```scheme
(define (factorial n)
  (define (fact-iter product counter)
    (if (> counter n)
        product
        (fact-iter (* counter product) (+ counter 1))))
  (fact-iter 1 1))
```

Now trace `(factorial 4)`:

```
(factorial 4)
(fact-iter 1 1)
(fact-iter 1 2)
(fact-iter 2 3)
(fact-iter 6 4)
(fact-iter 24 5)
24
```

No expansion and contraction. Each call immediately becomes the next call. The "product so far" is carried forward as an argument.

The key: the recursive call is in **tail position**—it's the last thing the function does. There's no pending operation waiting for the result.

---

## 6.12 Tail Call Optimization

A smart interpreter recognizes tail calls and **reuses the stack frame** instead of creating a new one:

```
WITHOUT TAIL CALL OPTIMIZATION:

(fact-iter 1 1)  → push frame
(fact-iter 1 2)  → push frame
(fact-iter 2 3)  → push frame
(fact-iter 6 4)  → push frame
(fact-iter 24 5) → push frame
24               → pop all frames

Stack grows with each call: O(n) space


WITH TAIL CALL OPTIMIZATION:

(fact-iter 1 1)  → use frame
(fact-iter 1 2)  → reuse frame
(fact-iter 2 3)  → reuse frame
(fact-iter 6 4)  → reuse frame
(fact-iter 24 5) → reuse frame
24               → return

Stack stays constant: O(1) space
```

With tail call optimization (TCO), tail recursion is as efficient as a loop. The Scheme standard **requires** TCO, which is why Scheme programmers use recursion freely.

Python doesn't have TCO—deep recursion will overflow the stack. JavaScript added TCO in ES6, but most browsers don't implement it. This is why loop constructs remain important in these languages.

---

## 6.13 Our Interpreter's Strategy

Let's be explicit about what our interpreter does:

```python
def evaluate(expression, env):
    # ...

    elif isinstance(expression, tuple):
        # Special forms first
        if expression[0] == "define":
            # Don't evaluate name
            env.define(expression[1], evaluate(expression[2], env))
            return None

        elif expression[0] == "if":
            # Only evaluate one branch
            if evaluate(expression[1], env):
                return evaluate(expression[2], env)
            return evaluate(expression[3], env)

        elif expression[0] == "lambda":
            # Don't evaluate body yet
            # ...

        # Ordinary application: evaluate ALL arguments
        proc = evaluate(expression[0], env)
        args = [evaluate(e, env) for e in expression[1:]]
        return proc(*args)
```

Key observations:

1. **Applicative order** for ordinary function calls—all arguments evaluated before application
2. **Special forms** break this pattern with custom rules
3. **No tail call optimization**—each recursive call uses a new Python stack frame

Our interpreter is simple and clear, but it will stack-overflow on deep recursion. A production interpreter would add TCO.

---

## 6.14 Implementing a Lazy Interpreter

For comparison, here's how a lazy interpreter might handle application:

```python
def evaluate_lazy(expression, env):
    # ...

    elif isinstance(expression, tuple):
        # Don't evaluate arguments yet - wrap them as thunks
        proc = evaluate_lazy(expression[0], env)
        thunks = [make_thunk(arg, env) for arg in expression[1:]]
        return proc(*thunks)

def make_thunk(expr, env):
    """Create a delayed computation."""
    cache = {}
    def force():
        if 'value' not in cache:
            cache['value'] = evaluate_lazy(expr, env)
        return cache['value']
    return force

def force(thunk_or_value):
    """Force a thunk, or return value unchanged."""
    if callable(thunk_or_value):
        return thunk_or_value()
    return thunk_or_value
```

Now arguments are wrapped as thunks. The function receives delayed computations and forces them only when needed.

---

## 6.15 A Complete Example

Let's trace through the problematic example with both strategies:

```scheme
(define (p) (p))
(define (test x y) (if (= x 0) 0 y))
(test 0 (p))
```

**Applicative Order (our interpreter):**

```
Step 1: Evaluate (test 0 (p))
        Need to evaluate arguments first

Step 2: Evaluate 0 → 0 ✓

Step 3: Evaluate (p)
        (p) = ((lambda () (p)))
        Call the lambda...

Step 4: Evaluate body: (p)
        (p) = ((lambda () (p)))
        Call the lambda...

Step 5: Evaluate body: (p)
        ... infinite loop, never reaches test!
```

**Normal Order (lazy):**

```
Step 1: Evaluate (test 0 (p))
        Don't evaluate arguments yet
        Pass thunks to test

Step 2: In test body: (if (= x 0) 0 y)
        x is thunk for 0
        y is thunk for (p)

Step 3: Evaluate (= x 0)
        Force x → 0
        (= 0 0) → true

Step 4: Condition is true, evaluate "then" branch
        → 0

Step 5: Return 0
        y (the thunk for (p)) is never forced!
```

---

## 6.16 Languages and Their Choices

Different languages make different choices:

| Language | Strategy | TCO? | Notes |
|----------|----------|------|-------|
| Scheme | Eager | Yes (required) | Special forms for laziness |
| Python | Eager | No | `itertools`, generators for laziness |
| JavaScript | Eager | Specified but rare | Promises for async laziness |
| Haskell | Lazy | Yes | Seq/bang for strictness |
| OCaml | Eager | Yes | `lazy` keyword available |
| Clojure | Eager | Limited | Lazy sequences built-in |

No choice is universally right. The best strategy depends on what you're building.

---

## Exercises

**6.1** Trace the evaluation of `(square (square (+ 1 1)))` under both applicative and normal order. Count how many additions are performed in each case.

**6.2** Write a `lazy-and` that short-circuits properly:

```scheme
(lazy-and false (/ 1 0))  ; Should return false, not error
```

Use thunks (zero-argument lambdas) for the arguments.

**6.3** Our interpreter doesn't have TCO. Write an iterative factorial in Python that our interpreter can call without stack overflow:

```python
def factorial_iter(n):
    result = 1
    while n > 1:
        result *= n
        n -= 1
    return result
```

Then add this as a builtin to the interpreter.

**6.4** The infinite loop example uses `(define (p) (p))`. What happens if you evaluate just `(p)` in our interpreter? Why?

**6.5** Implement a `delay` and `force` pair in our interpreter:

```scheme
(define delayed (delay (+ 1 2)))  ; Doesn't evaluate yet
(force delayed)                    ; Now evaluates → 3
(force delayed)                    ; Returns cached 3
```

Hint: `delay` should be a special form that wraps the expression in a thunk.

**6.6** Research: Why doesn't Python implement tail call optimization? What are the arguments for and against it? (Hint: look for Guido van Rossum's statements on this.)

---

## Summary

- **Applicative order** evaluates arguments before function application
- **Normal order** delays argument evaluation until values are needed
- Both give same results for pure computations, but can differ on termination
- **Special forms** like `if` need custom evaluation rules—can't evaluate all branches
- **Thunks** (zero-argument lambdas) simulate laziness in eager languages
- **Infinite data structures** are natural with lazy evaluation
- **Tail recursion** puts the recursive call in "last action" position
- **Tail call optimization** lets tail recursion use constant stack space
- Our interpreter uses applicative order with special forms, but no TCO
- The choice of evaluation strategy affects what programs you can write

In the final chapter, we'll step back and look at the journey from toy to production—types, errors, testing, and the path forward.
