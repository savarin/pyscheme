# Chapter 3: The Environment Model

If substitution cannot handle change, what replaces it? The answer is environments: data structures that map names to locations, where each location can hold a value that changes over time. This chapter explains how environments work, how they nest to create scope, and what we give up by moving from substitution to environments. The trade-off is real: environments enable mutation, but they also introduce complexity that substitution avoided.

---

## From Names to Locations

In the substitution model, a variable is a name for a value. When you write `(define x 2)`, the name `x` becomes an alias for `2`. Anywhere you see `x`, you can substitute `2`.

In the environment model, a variable is a name for a *location*. The location holds a value, but that value can change. When you write `(define x 2)`, you create a location, bind the name `x` to that location, and store `2` in it. Later, `(set! x 5)` stores a new value in the same location.

This is the key shift: variables are no longer aliases for values. They're names for places that can hold different values at different times.

---

## What Is an Environment?

An environment is a mapping from names to locations. You can think of it as a table:

```
┌──────────┬──────────┐
│  Name    │ Location │
├──────────┼──────────┤
│    x     │   → 2    │
│    y     │   → 5    │
│    +     │   → <fn> │
└──────────┴──────────┘
```

When we evaluate a symbol, we look it up in the current environment to find its location, then retrieve the value stored there.

When we assign with `set!`, we find the location and store a new value in it. The name still points to the same location—but the location now holds a different value.

---

## Scope and Nesting

Environments can be nested. When you define a procedure, it captures the environment where it was defined. When you call the procedure, a new environment is created for the procedure's parameters, with the captured environment as its *parent*.

```scheme
(define x 10)

(define (add-x y)
  (+ x y))

(add-x 5)  ; Returns 15
```

When we call `(add-x 5)`:

1. A new environment is created with `y` bound to `5`
2. This environment's parent is the environment where `add-x` was defined (which contains `x`)
3. When we evaluate `(+ x y)`, we find `y` in the current environment and `x` in the parent

This nesting is how lexical scope works. A procedure can access variables from its enclosing scope because it carries a reference to that scope's environment.

---

## How Assignment Works

With environments, assignment has a clear meaning:

1. Look up the name in the current environment (and its parents)
2. Find the location bound to that name
3. Store the new value in that location

```scheme
(define balance 100)

(define (withdraw amount)
  (set! balance (- balance amount))
  balance)
```

When we call `(withdraw 20)`:

1. We look up `balance` and find the location holding `100`
2. We compute `(- 100 20)` = `80`
3. We store `80` in that same location
4. We return `80`

The next call to `withdraw` will find `80` in that location, not `100`. The location persists; its contents change.

---

## The Cost of Mutation

Environments enable mutation, but they also introduce complexity.

**Order matters.** In the substitution model, `(+ (f 1) (g 2))` gives the same result regardless of whether we evaluate `(f 1)` or `(g 2)` first. With mutation, this might not be true—if `f` modifies a variable that `g` reads, the order of evaluation affects the result.

**Identity becomes ambiguous.** Are two variables "the same" if they hold the same value? Or only if they refer to the same location? Different answers lead to different notions of equality.

**Reasoning gets harder.** With substitution, you can understand a procedure by substitution—literally replacing parameters with arguments. With environments, you need to track what's in each location at each point in time.

---

## Two Worldviews

The substitution model and the environment model represent two different ways of thinking about computation.

**The functional worldview:** Programs are transformations of values. There is no "before" and "after"—only inputs and outputs. A procedure called with the same arguments always returns the same result. This makes programs easier to reason about, test, and parallelize.

**The imperative worldview:** Programs are sequences of actions that modify state. Variables hold values that change over time. This models the world more directly—bank balances do change, documents do get edited, games do progress.

Most languages support both styles to varying degrees. Scheme has both substitution-friendly features (procedures, recursion) and mutation (`set!`). The question isn't which model is "right" but which is appropriate for the problem at hand.

---

## Conclusion

The environment model is more powerful than substitution—it can express programs that change state over time. But that power comes at a cost. With environments, the order of operations matters. Identity becomes ambiguous. Reasoning about programs gets harder. This is the trade-off at the heart of programming language design: the simplicity of substitution versus the expressiveness of mutation. Neither is wrong; both have their place.
