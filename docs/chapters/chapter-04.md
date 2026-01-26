# Chapter 4: Everything is Procedures

We've seen where substitution breaks. Now let's see how far it goes. This chapter returns to the substitution model and pushes it to its logical extreme. Numbers can be represented as procedures. So can booleans. So can pairs and lists. This is Church encoding: the discovery that if data can be built from procedures, then procedures are the only primitive computation requires. It's similar to learning that every logic circuit reduces to NAND gates—a simplification that reveals something fundamental about what we're working with.

---

## Numbers as Procedures

What is a number? One answer: a number is how many times you do something.

Zero means "do it zero times"—which is the same as doing nothing. One means "do it once." Two means "do it twice." We can represent this directly with procedures:

```scheme
(define (zero f)
  (lambda (x) x))

(define (one f)
  (lambda (x) (f x)))

(define (two f)
  (lambda (x) (f (f x))))
```

Each number is a procedure that takes a function `f` and returns a new function. That new function applies `f` the appropriate number of times.

To see this work, we can apply these "numbers" to the increment function:

```scheme
> ((zero (lambda (x) (+ x 1))) 0)
0

> ((one (lambda (x) (+ x 1))) 0)
1

> ((two (lambda (x) (+ x 1))) 0)
2
```

The number `two`, applied to increment and starting from `0`, gives us `2`. The representation works.

---

## Increment and Arithmetic

If numbers are procedures, can we do arithmetic? Yes. Here's increment:

```scheme
(define (increment n)
  (lambda (f)
    (lambda (x) (f ((n f) x)))))
```

This takes a Church numeral `n` and returns a new Church numeral that applies `f` one more time. We can verify:

```scheme
> (((increment zero) (lambda (x) (+ x 1))) 0)
1

> (((increment one) (lambda (x) (+ x 1))) 0)
2
```

Addition, multiplication, and even subtraction can be defined similarly (though subtraction is surprisingly tricky). The point isn't to do practical arithmetic this way—it's to show that numbers don't need to be primitive. They can be built from procedures.

---

## Booleans as Procedures

What is a boolean? One answer: a boolean is a choice between two things.

True means "choose the first thing." False means "choose the second thing." We can represent this directly:

```scheme
(define (true x)
  (lambda (y) x))

(define (false x)
  (lambda (y) y))
```

`true` takes two arguments and returns the first. `false` takes two arguments and returns the second.

---

## Conditionals Without If

If booleans are procedures that choose, we don't need a special `if` form:

```scheme
(define (if-then-else condition)
  (lambda (then-clause)
    (lambda (else-clause)
      ((condition then-clause) else-clause))))
```

Let's try it:

```scheme
> (((if-then-else true) 2) 3)
2

> (((if-then-else false) 2) 3)
3
```

The built-in `if` is convenient, but not necessary. Booleans-as-procedures can do the same job.

---

## Pairs and Lists

What is a pair? One answer: a pair is something that holds two values and lets you retrieve either one.

We can represent this with procedures:

```scheme
(define (cons x y)
  (lambda (m) (m x y)))

(define (car z)
  (z (lambda (p q) p)))

(define (cdr z)
  (z (lambda (p q) q)))
```

A pair is a procedure that takes a selector function and applies it to the two values. `car` passes a selector that returns the first value. `cdr` passes a selector that returns the second.

```scheme
> (car (cons 1 2))
1

> (cdr (cons 1 2))
2
```

From pairs, we can build lists. From lists, we can build trees, tables, and any other data structure. All from procedures.

---

## What This Means

We started with two categories: procedures and data. We've now shown that data can be encoded as procedures:

- Numbers are procedures that apply a function some number of times
- Booleans are procedures that select between two options
- Pairs are procedures that apply a selector to two stored values

This is Church encoding, named after Alonzo Church, who developed these ideas in the 1930s as part of the lambda calculus.

The practical implications are limited—no one writes production code with Church numerals. But the conceptual implications are significant:

**Procedures are enough.** If numbers, booleans, and data structures can all be encoded as procedures, then procedures are the only primitive we need. Everything else is convenience.

**The boundary is arbitrary.** The distinction between "data" and "procedures" is not fundamental. It's a design choice that languages make for practical reasons—efficiency, readability, familiarity—but not because computation requires it.

**The interpreter was already complete.** Our sixty-line interpreter from Chapter 1 can evaluate Church numerals, Church booleans, and Church pairs without modification. It already had everything computation needs.

---

## Conclusion

Church encoding isn't practical—no one writes production code with Church numerals. But it reveals something important: the boundary between "data" and "procedures" is not as solid as it seems. Procedures are enough. Everything else is convenience. Understanding this won't change how you write code day to day, but it changes how you see it. The interpreter from Chapter 1, which seemed so minimal, was already complete. It had everything computation needs.
