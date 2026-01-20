# Chapter 4: State, Time + Identity

> *"We can model the world as a collection of separate, time-bound, interacting objects with state, or we can model the world as a single, timeless, stateless unity. Each view has powerful advantages, but neither alone is completely satisfactory. A grand unification has yet to emerge."*
> — Structure and Interpretation of Computer Programs

In the first three chapters, we built a pure functional interpreter. Expressions are evaluated, values are computed, and nothing changes. Each evaluation is independent of the others.

But the real world isn't like that. Bank balances change. Users log in and out. Files are written and deleted. The world has **state**—values that persist and mutate over time.

This chapter confronts that reality. We'll discover that our substitution model breaks down in the face of mutation, and we'll understand why environments aren't just an optimization—they're a necessity. We'll explore streams as an alternative to mutation, and we'll grapple with the deepest question in programming: what does it mean for something to be "the same"?

---

## 4.1 The World Changes

Consider a bank account. It has a balance that changes with deposits and withdrawals:

```scheme
(define balance 100)

(withdraw 20)    ; balance becomes 80
(withdraw 30)    ; balance becomes 50
(deposit 10)     ; balance becomes 60
```

This seems natural. It matches how we think about bank accounts in the real world. But it introduces something we've carefully avoided until now: **mutation**.

In our pure functional interpreter, evaluating an expression produces a value but doesn't change anything. The second evaluation of `(+ 2 3)` is identical to the first. But with a bank account:

```scheme
(withdraw 20)    ; first call: balance goes from 100 to 80
(withdraw 20)    ; second call: balance goes from 80 to 60
```

The same expression produces different results at different times. The world has changed between calls.

---

## 4.2 Introducing `set!`

Scheme uses `set!` (pronounced "set-bang") to change the value of an existing variable:

```scheme
(define balance 100)

(define (withdraw amount)
  (set! balance (- balance amount))
  balance)
```

The `set!` form doesn't create a new binding—it mutates an existing one. After `(set! balance 80)`, any future reference to `balance` sees `80`, not `100`.

```scheme
> balance
100

> (withdraw 20)
80

> balance
80

> (withdraw 30)
50
```

The variable `balance` is the same variable, but its value changes over time.

---

## 4.3 The Substitution Model Breaks

Let's try to evaluate `(withdraw 20)` using substitution, the model from Chapter 1.

The substitution model says: replace `balance` with its value `100`, then evaluate.

```scheme
(define (withdraw amount)
  (set! balance (- balance amount))
  balance)

; Substituting balance → 100:
(define (withdraw amount)
  (set! 100 (- 100 amount))
  100)
```

This is nonsense. `(set! 100 ...)` tries to assign to a number, not a variable. And even if it worked, the function would always return `100`.

The problem is fundamental: **substitution erases the identity of the variable**. Once we replace `balance` with `100`, we lose the ability to change what `balance` refers to. The name is gone; only the value remains.

```
┌───────────────────────────────────────────────────────────────┐
│  SUBSTITUTION MODEL                                           │
│                                                               │
│  (withdraw 20)                                                │
│       │                                                       │
│       ▼                                                       │
│  Replace 'balance' with 100                                   │
│       │                                                       │
│       ▼                                                       │
│  (set! 100 (- 100 20))   ← Makes no sense!                    │
│                                                               │
│  The name 'balance' has been destroyed.                       │
│  We can no longer change what it refers to.                   │
└───────────────────────────────────────────────────────────────┘
```

---

## 4.4 Why Environments Are Necessary

The environment model solves this. Instead of replacing names with values, we store bindings in a data structure and look them up at runtime.

```
┌───────────────────────────────────────────────────────────────┐
│  ENVIRONMENT MODEL                                            │
│                                                               │
│  Global Environment:                                          │
│  ┌─────────────────────────────────────┐                      │
│  │ "balance" ───────────► 100          │                      │
│  │ "withdraw" ──────────► <procedure>  │                      │
│  └─────────────────────────────────────┘                      │
│                                                               │
│  (withdraw 20)                                                │
│       │                                                       │
│       ▼                                                       │
│  Look up 'balance' → 100                                      │
│  Compute (- 100 20) → 80                                      │
│  MODIFY environment: balance → 80                             │
│  Return 80                                                    │
│                                                               │
│  Global Environment (after):                                  │
│  ┌─────────────────────────────────────┐                      │
│  │ "balance" ───────────► 80  ← Changed!                      │
│  │ "withdraw" ──────────► <procedure>  │                      │
│  └─────────────────────────────────────┘                      │
└───────────────────────────────────────────────────────────────┘
```

The key difference: **the name persists**. We can look up `balance`, get its current value, compute a new value, and store it back under the same name. The binding is mutable.

This is why we introduced environments in Chapter 2. For pure functional code, they're an optimization. For mutable code, they're essential.

---

## 4.5 Implementing `set!`

To support mutation, we need a new method on our `Environment` class:

```python
class Environment:
    def __init__(self, bindings=None, enclosing=None):
        self.bindings = bindings or {}
        self.enclosing = enclosing

    def define(self, symbol, value):
        """Create a new binding in this environment."""
        self.bindings[symbol] = value

    def get(self, symbol):
        """Look up a binding, searching enclosing scopes."""
        if symbol in self.bindings:
            return self.bindings[symbol]
        elif self.enclosing is not None:
            return self.enclosing.get(symbol)
        else:
            raise UndefinedSymbolError(f"Undefined symbol: '{symbol}'")

    def set(self, symbol, value):
        """Modify an existing binding, searching enclosing scopes."""
        if symbol in self.bindings:
            self.bindings[symbol] = value
        elif self.enclosing is not None:
            self.enclosing.set(symbol, value)
        else:
            raise UndefinedSymbolError(f"Cannot set undefined symbol: '{symbol}'")
```

Notice the difference between `define` and `set`:

- `define` always creates a binding in the **current** environment
- `set` searches up the chain and modifies **where the binding exists**

And in the evaluator:

```python
if expression[0] == "set!":
    symbol = expression[1]
    value = evaluate(expression[2], env)
    env.set(symbol, value)
    return None
```

---

## 4.6 The Consequences of Mutation

Mutation has profound consequences. Let's explore them.

### Order Matters

Without mutation, the order of independent expressions doesn't matter:

```scheme
; Pure functional - order irrelevant
(define a (+ 1 2))
(define b (* 3 4))
; a is 3, b is 12, regardless of order
```

With mutation, order is everything:

```scheme
(define x 1)

; Sequence A
(set! x (+ x 1))    ; x = 2
(set! x (* x 3))    ; x = 6

; Sequence B (reversed)
(set! x (* x 3))    ; x = 3
(set! x (+ x 1))    ; x = 4

; Different results!
```

The same operations in different orders yield different results. This makes programs harder to reason about.

### Functions Can Have Side Effects

A pure function always returns the same output for the same input. But with mutation:

```scheme
(define counter 0)

(define (next)
  (set! counter (+ counter 1))
  counter)

(next)    ; → 1
(next)    ; → 2
(next)    ; → 3
```

`next` takes no arguments, yet returns different values each time. It has a **side effect**—it modifies external state.

### Aliasing Creates Surprises

When two names refer to the same mutable object, changing one affects the other:

```scheme
(define account1 (make-account 100))
(define account2 account1)    ; Same account!

(withdraw account1 30)
(balance account2)    ; → 70, not 100!
```

This is called **aliasing**, and it's a common source of bugs.

---

## 4.7 Identity vs. Equality

Mutation forces us to confront a philosophical question: **what does it mean for two things to be equal?**

Consider:

```scheme
(define a (make-account 100))
(define b (make-account 100))

; Are a and b equal?
```

Both accounts have balance 100. In some sense they're equal. But:

```scheme
(withdraw a 50)
(balance a)    ; → 50
(balance b)    ; → 100
```

Changing `a` doesn't affect `b`. They're **different accounts** that happened to have the same initial balance.

This leads to two notions of equality:

- **Value equality**: Do they have the same contents right now?
- **Identity equality**: Are they the same object?

```
┌───────────────────────────────────────────────────────────────┐
│                                                               │
│   VALUE EQUALITY              IDENTITY EQUALITY               │
│                                                               │
│   ┌─────────┐ ┌─────────┐     ┌─────────┐                     │
│   │ bal=100 │ │ bal=100 │     │ bal=100 │                     │
│   └─────────┘ └─────────┘     └────┬────┘                     │
│       a           b                │                          │
│                                    ├── a                      │
│   Same value, different            │                          │
│   objects. Changing one            └── b                      │
│   doesn't affect the other.                                   │
│                               Same object, two names.         │
│                               Changing via 'a' is visible     │
│                               via 'b'.                        │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

Different languages handle this differently:

- Python: `==` for value, `is` for identity
- Java: `equals()` for value, `==` for identity
- JavaScript: `===` for... it's complicated

The need for multiple equality operators is a direct consequence of mutable state.

---

## 4.8 An Alternative: Streams

What if we could model change without mutation?

The idea: instead of a single value that changes over time, represent the **entire history of values** as a sequence.

```scheme
; Mutable approach: one balance that changes
(define balance 100)
(withdraw 20)    ; balance = 80
(withdraw 30)    ; balance = 50

; Stream approach: sequence of all balances
(define balance-history '(100 80 50 ...))
```

In the stream model, we don't mutate `balance`. Instead, we compute a new sequence that represents all the balances that ever were or will be.

```scheme
(define (make-balance-stream initial-balance transactions)
  (cons
    initial-balance
    (make-balance-stream
      (- initial-balance (car transactions))
      (cdr transactions))))
```

Given an initial balance and a stream of transactions, this produces the infinite stream of all balances.

```
Transactions: -20, -30, +10, ...

Balance stream:
  100 → 80 → 50 → 60 → ...
   │     │     │     │
   │     │     │     └─ after +10
   │     │     └─ after -30
   │     └─ after -20
   └─ initial
```

### Delayed Evaluation

Of course, we can't compute an infinite sequence all at once. The trick is **delayed evaluation**: we only compute elements when they're needed.

```scheme
(define (delay expr)
  (lambda () expr))

(define (force delayed)
  (delayed))

(define (cons-stream head tail-thunk)
  (cons head tail-thunk))

(define (stream-car s) (car s))
(define (stream-cdr s) (force (cdr s)))
```

A stream is a pair where:
- The `car` is the first element (computed immediately)
- The `cdr` is a **thunk**—a zero-argument function that, when called, produces the rest of the stream

This is lazy evaluation. We only compute what we need, when we need it.

---

## 4.9 Streams vs. State: A Comparison

Let's model the same system both ways.

**With mutable state:**

```scheme
(define balance 100)

(define (withdraw amount)
  (set! balance (- balance amount))
  balance)

(define (deposit amount)
  (set! balance (+ balance amount))
  balance)

; Usage
(withdraw 20)    ; → 80
(deposit 10)     ; → 90
(withdraw 30)    ; → 60
```

**With streams:**

```scheme
(define (make-account-stream balance transactions)
  (cons-stream
    balance
    (make-account-stream
      (process-transaction balance (stream-car transactions))
      (stream-cdr transactions))))

(define (process-transaction balance txn)
  (cond ((eq? (car txn) 'withdraw) (- balance (cdr txn)))
        ((eq? (car txn) 'deposit) (+ balance (cdr txn)))))

; Usage
(define transactions
  (cons-stream '(withdraw . 20)
    (cons-stream '(deposit . 10)
      (cons-stream '(withdraw . 30)
        ...))))

(define balances (make-account-stream 100 transactions))
; balances = 100, 80, 90, 60, ...
```

The stream version is more complex, but it has advantages:

| Mutable State | Streams |
|---------------|---------|
| Simple mental model | More complex |
| Destructive updates | All history preserved |
| Hard to parallelize | Naturally parallel |
| Order-dependent | Order-independent |
| Current value only | Time-travel possible |

---

## 4.10 The Time Problem

The fundamental issue is **time**.

In the physical world, things change. My bank balance at 9 AM is different from my balance at 5 PM. This seems to require mutable state—a single variable that takes different values at different times.

But there's another perspective. Instead of thinking "the balance changes," we can think "there are many balances, one for each moment in time." The balance-at-9-AM and the balance-at-5-PM are different values in a sequence.

This is the stream view: we model time explicitly as a dimension of the data, rather than implicitly through mutation.

```
MUTABLE VIEW:
─────────────────────────────────────────────────────────────────►
  balance = 100     balance = 80     balance = 50     time
              │                │                │
              └── withdraw ────┴── withdraw ────┘

STREAM VIEW:
─────────────────────────────────────────────────────────────────►
  balance₀ = 100 ─► balance₁ = 80 ─► balance₂ = 50   time

  All values exist simultaneously in the stream.
```

---

## 4.11 The Trade-offs

SICP dedicates considerable space to this tension because there's no clear winner.

**Arguments for mutable state:**

- Matches how we naturally think about objects
- More efficient for single-value updates
- Simpler code for many use cases
- Direct correspondence to hardware memory

**Arguments for streams/immutability:**

- Easier to reason about (no hidden state changes)
- Naturally supports undo, replay, debugging
- Better for concurrency (no race conditions)
- Enables powerful optimizations (memoization, laziness)

Real programs use both. A web server might use mutable state for database connections but immutable data structures for processing requests. A game might use mutable state for performance-critical physics but functional streams for event handling.

---

## 4.12 Concurrency: Where Mutation Hurts

The problems with mutable state multiply in concurrent programs.

Consider two processes trying to withdraw from the same account:

```
Process A: (withdraw 50)
Process B: (withdraw 30)

Initial balance: 100
Expected final balance: 20
```

But with mutable state and unfortunate timing:

```
Time │ Process A              │ Process B              │ Balance
─────┼────────────────────────┼────────────────────────┼─────────
  1  │ read balance → 100     │                        │ 100
  2  │                        │ read balance → 100     │ 100
  3  │ compute 100-50 = 50    │                        │ 100
  4  │                        │ compute 100-30 = 70    │ 100
  5  │ write balance ← 50     │                        │ 50
  6  │                        │ write balance ← 70     │ 70
─────┴────────────────────────┴────────────────────────┴─────────

Final balance: 70 (should be 20!)
```

Both processes read the old balance before either writes. One write clobbers the other. Money has been created from nothing.

This is a **race condition**, and it's notoriously hard to debug. The bug only appears with specific timing, which may be rare in testing but common in production.

Immutable data doesn't have this problem:

```
Process A: new_balance_a = balance - 50
Process B: new_balance_b = balance - 30

Both computations use the same input (100).
Neither modifies shared state.
A separate process can combine the results correctly.
```

---

## 4.13 The SICP Perspective

At the end of Chapter 3, SICP offers this meditation:

> *"We can model the world as a collection of separate, time-bound, interacting objects with state, or we can model the world as a single, timeless, stateless unity. Each view has powerful advantages, but neither alone is completely satisfactory. A grand unification has yet to emerge."*

This was written in 1985. Four decades later, the grand unification still hasn't emerged. Languages continue to offer both paradigms:

- **Haskell**: Pure by default, explicit effects
- **Clojure**: Immutable by default, controlled mutation
- **Rust**: Ownership system to manage mutation safely
- **JavaScript**: Mutable by default, functional libraries

The tension is fundamental, not accidental. Both views capture something true about computation.

---

## 4.14 What Our Interpreter Supports

Our pyscheme interpreter, in its minimal form, is pure functional. It doesn't include `set!`. All bindings are immutable once created.

The Claude version could support `set!` by adding the `set` method to `Environment` and the evaluator clause shown earlier. But we've chosen not to, keeping the interpreter in the pure functional world.

This is a pedagogical choice. Understanding pure functional programming first makes the costs of mutation clearer when you encounter them.

---

## 4.15 Summary of Models

Let's recap the models we've seen:

```
┌─────────────────────────────────────────────────────────────────┐
│  SUBSTITUTION MODEL (Chapters 1, 3)                             │
│                                                                 │
│  • Replace names with values                                    │
│  • Works for pure functional code                               │
│  • Breaks with mutation (can't substitute into set!)            │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│  ENVIRONMENT MODEL (Chapters 2, 3, 4)                           │
│                                                                 │
│  • Store bindings in data structure                             │
│  • Look up names at runtime                                     │
│  • Supports mutation via set method                             │
│  • Required for stateful programs                               │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│  STREAM MODEL (Chapter 4)                                       │
│                                                                 │
│  • Represent change as sequence of values                       │
│  • No mutation—all values coexist                               │
│  • Requires lazy evaluation                                     │
│  • Elegant but can be complex                                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

Each model is a lens for understanding computation. The substitution model is simple and intuitive. The environment model is practical and powerful. The stream model is elegant and principled.

---

## Exercises

**4.1** Implement `set!` in the interpreter by adding a `set` method to `Environment` and an evaluator clause. Test it with the bank account example.

**4.2** What happens if you try to `set!` a variable that doesn't exist? Should it create the variable (like JavaScript's implicit globals) or raise an error (like Python)? Implement your choice and justify it.

**4.3** Consider this code:

```scheme
(define (make-counter)
  (define count 0)
  (lambda ()
    (set! count (+ count 1))
    count))

(define c1 (make-counter))
(define c2 (make-counter))
```

Draw the environment diagram. Are `c1` and `c2` independent? Why or why not?

**4.4** Implement a simple stream library with `cons-stream`, `stream-car`, and `stream-cdr`. Use it to create an infinite stream of natural numbers.

**4.5** The function `(define (f x) (set! x 10))` appears to modify its parameter. What actually happens when you call `(f 5)` and then evaluate `5`? Explain using the environment model.

**4.6** Write two versions of a function that computes a running sum:
   - A mutable version using `set!`
   - A pure functional version using recursion

   Compare their clarity and ease of testing.

---

## Summary

- **Mutation** changes the value bound to a name over time
- The **substitution model** breaks with mutation (can't substitute into `set!`)
- The **environment model** supports mutation via a `set` method
- Mutation introduces **order dependence**, **side effects**, and **aliasing**
- **Identity vs. equality** becomes a real distinction
- **Streams** offer an alternative: model change as sequences, not mutation
- **Concurrency** makes mutation's problems worse (race conditions)
- Neither pure mutation nor pure immutability is always best
- The tension between them is **fundamental to programming**

In the next chapter, we'll explore the ultimate minimalism: lambda calculus. We'll see how numbers, booleans, and data structures can all be built from pure functions—no primitives, no `set!`, just lambda.
