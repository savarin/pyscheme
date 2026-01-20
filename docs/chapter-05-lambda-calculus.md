# Chapter 5: Lambda Calculus — Computation from Nothing

> *"All you need is lambda."*

In the 1930s, before computers existed, mathematician Alonzo Church invented a formal system to study computation. He called it the **lambda calculus**. It has only three elements:

1. **Variables**: `x`, `y`, `z`, ...
2. **Abstraction**: `λx.body` (creating a function)
3. **Application**: `(f x)` (calling a function)

That's it. No numbers. No booleans. No data structures. No `if`. No loops. Just variables, function creation, and function application.

And yet—this is enough to compute anything computable.

In this chapter, we'll prove it. We'll build numbers, booleans, conditionals, and data structures using nothing but lambda. Along the way, you'll experience what David Beazley's SICP students describe as the moment their minds were blown.

---

## 5.1 The Minimal Language

Let's be clear about what we're allowing ourselves:

```
ALLOWED:
  λx.body    — Create a function with parameter x
  (f x)      — Apply function f to argument x
  x          — Reference a variable

NOT ALLOWED:
  Numbers (1, 2, 3, ...)
  Arithmetic (+, -, *, /)
  Booleans (true, false)
  Conditionals (if)
  Data structures (pairs, lists)
```

Our Scheme interpreter has built-in numbers and `if`. The challenge: can we implement these using only `lambda`?

The answer, as Church proved, is yes.

---

## 5.2 Church Numerals: Numbers as Functions

How do you represent a number without having numbers?

Church's insight: a number is **how many times** you do something.

- **Zero** means "don't do it at all"
- **One** means "do it once"
- **Two** means "do it twice"
- **Three** means "do it three times"

More precisely: a Church numeral is a function that takes another function `f` and applies it a certain number of times.

### Zero

Zero applies `f` zero times—it just returns its argument unchanged:

```scheme
(define zero
  (lambda (f)
    (lambda (x) x)))
```

Given any function `f`, `zero` returns the identity function. The `f` is ignored.

```
zero = λf. λx. x

(zero f) = λx. x      ; Returns identity, regardless of f
((zero f) x) = x      ; Apply to x, get x back
```

### One

One applies `f` exactly once:

```scheme
(define one
  (lambda (f)
    (lambda (x) (f x))))
```

```
one = λf. λx. (f x)

(one f) = λx. (f x)       ; Returns "apply f once"
((one f) x) = (f x)       ; Apply to x, get (f x)
```

### Two

Two applies `f` twice:

```scheme
(define two
  (lambda (f)
    (lambda (x) (f (f x)))))
```

```
two = λf. λx. (f (f x))

(two f) = λx. (f (f x))         ; Returns "apply f twice"
((two f) x) = (f (f x))         ; Apply to x, get f(f(x))
```

### The Pattern

Do you see it? The number `n` is represented by a function that applies `f` exactly `n` times:

```
zero  = λf. λx. x                    ; f applied 0 times
one   = λf. λx. (f x)                ; f applied 1 time
two   = λf. λx. (f (f x))            ; f applied 2 times
three = λf. λx. (f (f (f x)))        ; f applied 3 times
four  = λf. λx. (f (f (f (f x))))    ; f applied 4 times
```

---

## 5.3 Converting Church Numerals to Regular Numbers

To see that these really represent numbers, we can apply them to an increment function:

```scheme
; Apply a Church numeral to (+1) starting from 0
(define (church-to-int n)
  ((n (lambda (x) (+ x 1))) 0))
```

Let's trace through:

```scheme
(church-to-int zero)
= ((zero (lambda (x) (+ x 1))) 0)
= ((λx. x) 0)                        ; zero ignores the function
= 0                                  ✓

(church-to-int one)
= ((one (lambda (x) (+ x 1))) 0)
= ((λx. ((lambda (x) (+ x 1)) x)) 0)
= ((lambda (x) (+ x 1)) 0)           ; apply increment once
= (+ 0 1)
= 1                                  ✓

(church-to-int two)
= ((two (lambda (x) (+ x 1))) 0)
= ((lambda (x) (+ x 1)) ((lambda (x) (+ x 1)) 0))
= ((lambda (x) (+ x 1)) 1)           ; apply increment twice
= 2                                  ✓
```

In our interpreter:

```python
>>> zero = ("lambda", ("f",), ("lambda", ("x",), "x"))
>>> one = ("lambda", ("f",), ("lambda", ("x",), ("f", "x")))
>>> two = ("lambda", ("f",), ("lambda", ("x",), ("f", ("f", "x"))))

>>> inc = ("lambda", ("x",), ("+", "x", 1))

>>> evaluate((("zero", inc), 0))
0
>>> evaluate((("one", inc), 0))
1
>>> evaluate((("two", inc), 0))
2
```

The Church numerals work.

---

## 5.4 Increment: Building Numbers

We defined `zero`, `one`, `two` directly. But we can also define **increment**—a function that takes a Church numeral and returns the next one.

```scheme
(define increment
  (lambda (n)
    (lambda (f)
      (lambda (x)
        (f ((n f) x))))))
```

This is dense. Let's unpack it:

- `n` is a Church numeral (a function that applies `f` some number of times)
- We return a new Church numeral
- The new numeral applies `f` one more time than `n` did

```
increment n = λf. λx. (f ((n f) x))
                       │    └──── n applies f some number of times
                       └──── we apply f one more time
```

Let's verify:

```scheme
(increment zero)
= (λf. λx. (f ((zero f) x)))
= (λf. λx. (f ((λx. x) x)))          ; (zero f) = identity
= (λf. λx. (f x))
= one                                 ✓

(increment one)
= (λf. λx. (f ((one f) x)))
= (λf. λx. (f ((λx. (f x)) x)))
= (λf. λx. (f (f x)))
= two                                 ✓
```

Now we can build any number:

```scheme
(define three (increment two))
(define four (increment three))
(define five (increment four))
; ... and so on
```

In our interpreter:

```python
>>> increment = ("lambda", ("n",),
...     ("lambda", ("f",),
...         ("lambda", ("x",), ("f", (("n", "f"), "x")))))

>>> evaluate(("define", "zero", zero))
>>> evaluate(("define", "increment", increment))

>>> evaluate(((("increment", "zero"), inc), 0))
1
>>> evaluate(((("increment", ("increment", "zero")), inc), 0))
2
```

---

## 5.5 Addition and Multiplication

Once we have increment, we can define addition:

```scheme
(define add
  (lambda (m n)
    ((m increment) n)))
```

Adding `m` to `n` means incrementing `n` exactly `m` times. Since `m` is a Church numeral that applies a function `m` times, we pass it `increment` and `n`.

```
(add two three)
= ((two increment) three)
= (increment (increment three))      ; increment three twice
= (increment four)
= five                               ✓
```

Multiplication is similar:

```scheme
(define multiply
  (lambda (m n)
    (lambda (f)
      (m (n f)))))
```

Multiplying `m` times `n` means: applying `f` `n` times, and doing that `m` times.

```
(multiply two three)
= λf. (two (three f))
= λf. (two (λx. (f (f (f x)))))      ; three applies f 3 times
= λf. (λx. (three (three x)))        ; wait, that's not right...

; Let's be more careful:
(multiply two three)
= λf. (two (three f))

; (three f) = λx. (f (f (f x)))  — applies f 3 times
; (two g)   = λx. (g (g x))      — applies g 2 times

; (two (three f))
; = λx. ((three f) ((three f) x))
; = λx. ((three f) (f (f (f x))))
; = λx. (f (f (f (f (f (f x))))))    — applies f 6 times
= six                                ✓
```

---

## 5.6 Church Booleans: True and False as Functions

Numbers aren't the only thing we can encode. What about booleans?

Church's encoding is elegant:

- **True** takes two arguments and returns the **first**
- **False** takes two arguments and returns the **second**

```scheme
(define true
  (lambda (x)
    (lambda (y) x)))

(define false
  (lambda (x)
    (lambda (y) y)))
```

```
true  = λx. λy. x     ; Returns first argument
false = λx. λy. y     ; Returns second argument
```

Why is this useful? Because it gives us conditionals for free!

---

## 5.7 If as a Function

With Church booleans, `if` is trivial:

```scheme
(define if-then-else
  (lambda (condition)
    (lambda (then-branch)
      (lambda (else-branch)
        ((condition then-branch) else-branch)))))
```

If `condition` is `true`, it selects the first argument (`then-branch`).
If `condition` is `false`, it selects the second argument (`else-branch`).

```scheme
(((if-then-else true) 2) 3)
= ((true 2) 3)
= ((λy. 2) 3)              ; true returns first argument
= 2                        ✓

(((if-then-else false) 2) 3)
= ((false 2) 3)
= ((λy. y) 3)              ; false returns second argument
= 3                        ✓
```

In our interpreter:

```python
>>> true = ("lambda", ("x",), ("lambda", ("y",), "x"))
>>> false = ("lambda", ("x",), ("lambda", ("y",), "y"))
>>> if_proc = ("lambda", ("f",),
...     ("lambda", ("a",),
...         ("lambda", ("b",), (("f", "a"), "b"))))

>>> evaluate(("define", "true", true))
>>> evaluate(("define", "false", false))
>>> evaluate(("define", "if_procedure", if_proc))

>>> evaluate(((("if_procedure", "true"), 2), 3))
2
>>> evaluate(((("if_procedure", "false"), 2), 3))
3
```

We've implemented `if` using only `lambda`.

---

## 5.8 Boolean Operations

With Church booleans, we can define `and`, `or`, and `not`:

```scheme
(define and
  (lambda (p q)
    ((p q) false)))
```

If `p` is true, return `q` (which might be true or false).
If `p` is false, return false.

```scheme
(define or
  (lambda (p q)
    ((p true) q)))
```

If `p` is true, return true.
If `p` is false, return `q`.

```scheme
(define not
  (lambda (p)
    ((p false) true)))
```

If `p` is true, return false.
If `p` is false, return true.

Let's verify `not`:

```scheme
(not true)
= ((true false) true)
= ((λy. false) true)       ; true selects first argument (false)
= false                    ✓

(not false)
= ((false false) true)
= ((λy. y) true)           ; false selects second argument (true)
= true                     ✓
```

---

## 5.9 Pairs: Data Structures from Functions

We can also build data structures. A pair holds two values and lets us extract either one.

```scheme
(define cons
  (lambda (x y)
    (lambda (m) (m x y))))

(define car
  (lambda (z)
    (z (lambda (p q) p))))

(define cdr
  (lambda (z)
    (z (lambda (p q) q))))
```

The encoding:
- `cons` creates a function that "holds" `x` and `y` in a closure
- `car` passes a selector that extracts the first element
- `cdr` passes a selector that extracts the second element

```
(cons 1 2) = λm. (m 1 2)

(car (cons 1 2))
= (car (λm. (m 1 2)))
= ((λm. (m 1 2)) (λp q. p))        ; pass in "select first"
= ((λp q. p) 1 2)
= 1                                ✓

(cdr (cons 1 2))
= (cdr (λm. (m 1 2)))
= ((λm. (m 1 2)) (λp q. q))        ; pass in "select second"
= ((λp q. q) 1 2)
= 2                                ✓
```

In our interpreter:

```python
>>> cons = ("lambda", ("x", "y"), ("lambda", ("m",), ("m", "x", "y")))
>>> car = ("lambda", ("z",), ("z", ("lambda", ("p", "q"), "p")))
>>> cdr = ("lambda", ("z",), ("z", ("lambda", ("p", "q"), "q")))

>>> evaluate(("define", "cons", cons))
>>> evaluate(("define", "car", car))
>>> evaluate(("define", "cdr", cdr))

>>> evaluate(("car", ("cons", 1, 2)))
1
>>> evaluate(("cdr", ("cons", 1, 2)))
2
```

With pairs, we can build lists, trees, and any data structure we want.

---

## 5.10 The Revelation

Let's pause and appreciate what we've done.

We started with **only lambda**—function creation and application. No built-in numbers, no booleans, no data structures.

And we built:

| Concept | Church Encoding |
|---------|-----------------|
| Zero | `λf. λx. x` |
| One | `λf. λx. (f x)` |
| Two | `λf. λx. (f (f x))` |
| Increment | `λn. λf. λx. (f ((n f) x))` |
| True | `λx. λy. x` |
| False | `λx. λy. y` |
| If | `λc. λt. λe. ((c t) e)` |
| Pair | `λx. λy. λm. (m x y)` |
| First | `λz. (z (λp. λq. p))` |
| Second | `λz. (z (λp. λq. q))` |

These aren't simulations or tricks. Church proved that lambda calculus is **Turing complete**—it can compute anything that any computer can compute.

The building blocks of computation aren't numbers and booleans. They're **functions**.

```
┌───────────────────────────────────────────────────────────┐
│                                                           │
│                   THE INSIGHT                             │
│                                                           │
│       Data and procedures are not fundamentally           │
│       different. Data can be encoded as procedures.       │
│       All you need is lambda.                             │
│                                                           │
└───────────────────────────────────────────────────────────┘
```

---

## 5.11 What About Recursion?

We can build numbers, booleans, and pairs. But we've been using `define` to name things. Can we do recursion without names?

Consider factorial:

```scheme
(define factorial
  (lambda (n)
    (if (= n 0)
        1
        (* n (factorial (- n 1))))))
```

The function refers to itself by name. But what if we don't have `define`?

This is where the **Y combinator** comes in:

```scheme
(define Y
  (lambda (f)
    ((lambda (x) (f (lambda (y) ((x x) y))))
     (lambda (x) (f (lambda (y) ((x x) y)))))))
```

The Y combinator is a **fixed-point combinator**. Given a function `f`, it returns a value `x` such that `x = (f x)`.

For recursion, we write our function to take an extra argument—the function to call for recursion:

```scheme
(define factorial-step
  (lambda (recurse)
    (lambda (n)
      (if (= n 0)
          1
          (* n (recurse (- n 1)))))))

; Then:
(define factorial (Y factorial-step))
```

The Y combinator "ties the knot," making `recurse` refer back to the whole function.

This is advanced material, and the Y combinator is notoriously mind-bending. The point is: **recursion doesn't require named functions**. It can be encoded in pure lambda calculus.

---

## 5.12 Testing It All in Our Interpreter

Let's verify everything works in our pyscheme interpreter:

```python
# Church numerals
zero = ("lambda", ("f",), ("lambda", ("x",), "x"))
one = ("lambda", ("f",), ("lambda", ("x",), ("f", "x")))
two = ("lambda", ("f",), ("lambda", ("x",), ("f", ("f", "x"))))
increment = ("lambda", ("n",),
    ("lambda", ("f",),
        ("lambda", ("x",), ("f", (("n", "f"), "x")))))

# Test function (convert to regular int)
inc = ("lambda", ("x",), ("+", "x", 1))

# Church booleans
true = ("lambda", ("x",), ("lambda", ("y",), "x"))
false = ("lambda", ("x",), ("lambda", ("y",), "y"))
if_proc = ("lambda", ("f",),
    ("lambda", ("a",),
        ("lambda", ("b",), (("f", "a"), "b"))))

# Pairs
cons = ("lambda", ("x", "y"), ("lambda", ("m",), ("m", "x", "y")))
car = ("lambda", ("z",), ("z", ("lambda", ("p", "q"), "p")))
cdr = ("lambda", ("z",), ("z", ("lambda", ("p", "q"), "q")))

# Define everything
for name, val in [("zero", zero), ("one", one), ("two", two),
                   ("increment", increment), ("true", true),
                   ("false", false), ("if_procedure", if_proc),
                   ("cons", cons), ("car", car), ("cdr", cdr)]:
    evaluate(("define", name, val))

# Test Church numerals
assert evaluate((("zero", inc), 0)) == 0
assert evaluate((("one", inc), 0)) == 1
assert evaluate((("two", inc), 0)) == 2
assert evaluate(((("increment", "zero"), inc), 0)) == 1
assert evaluate(((("increment", ("increment", "zero")), inc), 0)) == 2

# Test Church booleans
assert evaluate(((("if_procedure", "true"), 2), 3)) == 2
assert evaluate(((("if_procedure", "false"), 2), 3)) == 3

# Test pairs
assert evaluate(("car", ("cons", 1, 2))) == 1
assert evaluate(("cdr", ("cons", 1, 2))) == 2

print("All Church encoding tests pass!")
```

Every test passes. We've implemented numbers, booleans, conditionals, and pairs using nothing but lambda.

---

## 5.13 Historical Context

Alonzo Church developed lambda calculus in the 1930s as part of research into the foundations of mathematics. He was trying to answer the question: "What does it mean for a problem to be computable?"

Around the same time, Alan Turing developed the Turing machine—a different model of computation based on a tape and a read/write head.

In 1936, Church and Turing independently proved that their models were equivalent. Anything computable by a Turing machine is computable in lambda calculus, and vice versa.

This equivalence is profound. It suggests that "computability" is a fundamental concept, not an artifact of a particular model.

```
┌────────────────────────────────────────────────────────┐
│                                                        │
│  1936: Church-Turing Thesis                            │
│                                                        │
│  ┌─────────────┐    equivalent    ┌─────────────┐      │
│  │   Lambda    │◄────────────────►│   Turing    │      │
│  │  Calculus   │                  │   Machine   │      │
│  └─────────────┘                  └─────────────┘      │
│                                                        │
│  Both define the same set of computable functions.     │
│  "Computability" is a natural, universal concept.      │
│                                                        │
└────────────────────────────────────────────────────────┘
```

Lambda calculus became the foundation of functional programming. Lisp (1958) was directly inspired by it. Scheme, ML, Haskell, and every modern functional language carries its DNA.

---

## 5.14 Why This Matters

You might wonder: why learn Church encodings? We have perfectly good built-in numbers and booleans.

Three reasons:

### 1. Understanding Abstraction

Church encodings reveal that the boundary between "data" and "code" is arbitrary. Data is just code we've agreed to treat specially. This insight liberates you to think more creatively about program design.

### 2. Understanding Language Design

Knowing that everything can be built from lambda helps you understand why functional languages are designed the way they are. Features like closures, higher-order functions, and lazy evaluation aren't arbitrary—they're consequences of a deep theory.

### 3. The Joy of Discovery

There's something magical about realizing that `λx. λy. x` represents truth. It's a moment when mathematics and programming touch something universal about computation.

As one of Beazley's SICP students put it: "Numbers as procedures. Take a moment to let that sink in..."

---

## 5.15 What We Left Out

Lambda calculus is vast. Topics we didn't cover:

- **Subtraction and division** (surprisingly tricky with Church numerals)
- **Predecessor function** (getting the previous number)
- **Lists** (as nested pairs)
- **Recursion combinators** (Y, Z, and others)
- **Types** (simply-typed lambda calculus, System F)
- **Reduction strategies** (normal order, applicative order)
- **Confluence** (the Church-Rosser theorem)

Each of these could fill a chapter of its own. The rabbit hole goes deep.

---

## Exercises

**5.1** Define Church numeral `three` directly (without using increment), and verify it converts to 3.

**5.2** Implement `is-zero`—a function that returns `true` if a Church numeral is zero, `false` otherwise. (Hint: what happens when you apply zero to anything?)

**5.3** The pair encoding uses closures to hold values. Draw the environment diagram for `(cons 1 2)` and trace through `(car (cons 1 2))`.

**5.4** Implement `and`, `or`, and `not` for Church booleans and test them in the interpreter.

**5.5** Research the **predecessor function** for Church numerals (getting `n-1` from `n`). It's famously tricky. Why is subtraction harder than addition in this encoding?

**5.6** Implement lists using pairs:
   - `nil` (empty list)
   - `(cons x list)` (add element to front)
   - `(is-nil list)` (test for empty)
   - `(head list)` (first element)
   - `(tail list)` (rest of list)

---

## Summary

- **Lambda calculus** has only three elements: variables, abstraction, application
- **Church numerals** encode numbers as repeated function application
- **Church booleans** encode true/false as selector functions
- **Pairs** can be built from closures
- **All** of this works in our interpreter—it's not just theory
- Lambda calculus and Turing machines are **equivalent** in power
- The insight: **data can be encoded as procedures**

In the next chapter, we'll explore evaluation strategies—applicative vs. normal order—and discover why our `if` special form must be special, and how laziness enables infinite data structures.
