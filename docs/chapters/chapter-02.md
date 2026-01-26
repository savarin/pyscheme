# Chapter 2: Where Substitution Breaks

The substitution model handles a surprising amount: recursion, higher-order functions, even complex nested expressions. But it has a fundamental limitation. The moment you need a value to change over time—a counter that increments, a balance that decreases—substitution fails. This chapter examines exactly why. The problem isn't a bug in our implementation; it's a fundamental mismatch between substitution and the concept of change.

---

## A Bank Account

Consider modeling a bank account. We want a `withdraw` procedure that reduces the balance and returns the new amount:

```scheme
(define balance 100)

(define (withdraw amount)
  (set! balance (- balance amount))
  balance)
```

```scheme
> (withdraw 20)
80

> (withdraw 20)
60

> (withdraw 20)
40
```

Each call to `withdraw` returns a different value. The balance *changes*. This is exactly what we'd expect from a bank account—and exactly what substitution cannot express.

---

## The Problem with Assignment

In Scheme, `set!` changes the value of an existing variable. Let's try to understand what happens when we apply substitution to the `withdraw` procedure.

If `balance` is `100`, substitution would replace every occurrence of `balance` with `100`:

```scheme
(define (withdraw amount)
  (set! 100 (- 100 amount))  ; This doesn't make sense
  100)                        ; Always returns 100
```

The model breaks. We can't substitute `balance` with its value because the whole point is that `balance` holds different values at different times.

---

## Before and After

The core problem is that substitution treats all occurrences of a variable as identical. It cannot distinguish:

- The balance *before* a withdrawal
- The balance *after* a withdrawal

Both are just `balance`. But they're different values. At 10:00 AM, `balance` might be `100`. At 10:01 AM, after a withdrawal, `balance` might be `80`. Substitution has no way to represent this.

In the substitution model, calling a procedure with the same arguments always produces the same result. That's a feature when you want predictability—you can reason about programs by substitution. But it's a limitation when you need to model things that change.

---

## What Substitution Cannot Express

The bank account example reveals a category of programs that substitution cannot handle: any program where calling the same procedure twice produces different results.

This includes:

- Counters that increment
- Random number generators
- Any interaction with the outside world (reading input, getting the current time)
- Objects with internal state

These aren't exotic edge cases. They're fundamental to most real programs. A web server that handles requests, a game that tracks score, a text editor that tracks the document—all require some form of state.

---

## The Fork in the Road

We now face a choice that divides programming languages and programming styles.

**One path: avoid mutation.** Stay in the world of substitution. Model change not by mutating variables but by creating new values. A withdrawal doesn't change the balance; it produces a *new* balance. This is the functional programming approach. It preserves the ability to reason by substitution, at the cost of modeling state less directly.

**The other path: embrace mutation.** Accept that variables can change over time. Replace substitution with a more powerful model that can track these changes. This is the imperative programming approach. It models state directly, at the cost of losing the simplicity of substitution.

Neither path is wrong. Both have trade-offs. But once you introduce mutation, you need a different mental model for how programs execute. That model is based on environments, which we turn to next.

---

## Conclusion

Substitution treats all occurrences of a variable as identical—it cannot distinguish the balance before a withdrawal from the balance after. To model change, we need a different mechanism: one where variables are not just names for values, but names for locations that can hold different values at different times. That mechanism is the environment model, which we turn to next.
