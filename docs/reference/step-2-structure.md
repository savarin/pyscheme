# Step 2: Chapter Structure

For each chapter: introduction (1 paragraph), conclusion (1 paragraph), and subsection names.

---

## Chapter 1: The Substitution Model

### Introduction

This chapter builds a working interpreter in about sixty lines of Python. The interpreter is based on a single idea: computation is the mechanical replacement of symbols. When you call a function, you substitute arguments into the body. When you reference a variable, you substitute its value. When you evaluate a conditional, you pick one branch and discard the other. By the end of the chapter, you'll have an interpreter that handles variables, conditionals, functions, recursion, and higher-order functions—enough to compute Fibonacci numbers, enough to trace any expression step by step on paper.

### Subsections

1. What Is Computation?
2. Primitives and Symbols
3. The Evaluate Function
4. Special Forms: Define, If, Lambda
5. Procedure Application
6. Putting It Together
7. Fibonacci: A Proof It Works

### Conclusion

The substitution model is complete. You now have a mental model precise enough to execute programs by hand—no hidden machinery, no mysterious runtime, just symbols replacing symbols until a value emerges. The interpreter we built is small, but it handles the core of what any language must handle. In the next chapter, we'll see where this model breaks.

---

## Chapter 2: Where Substitution Breaks

### Introduction

The substitution model handles a surprising amount: recursion, higher-order functions, even complex nested expressions. But it has a fundamental limitation. The moment you need a value to change over time—a counter that increments, a balance that decreases—substitution fails. This chapter examines exactly why. The problem isn't a bug in our implementation; it's a fundamental mismatch between substitution and the concept of change.

### Subsections

1. A Bank Account
2. The Problem with Assignment
3. Before and After
4. What Substitution Cannot Express
5. The Fork in the Road

### Conclusion

Substitution treats all occurrences of a variable as identical—it cannot distinguish the balance before a withdrawal from the balance after. To model change, we need a different mechanism: one where variables are not just names for values, but names for locations that can hold different values at different times. That mechanism is the environment model, which we turn to next.

---

## Chapter 3: The Environment Model

### Introduction

If substitution cannot handle change, what replaces it? The answer is environments: data structures that map names to locations, where each location can hold a value that changes over time. This chapter explains how environments work, how they nest to create scope, and what we give up by moving from substitution to environments. The trade-off is real: environments enable mutation, but they also introduce complexity that substitution avoided.

### Subsections

1. From Names to Locations
2. What Is an Environment?
3. Scope and Nesting
4. How Assignment Works
5. The Cost of Mutation
6. Two Worldviews

### Conclusion

The environment model is more powerful than substitution—it can express programs that change state over time. But that power comes at a cost. With environments, the order of operations matters. Identity becomes ambiguous. Reasoning about programs gets harder. This is the trade-off at the heart of programming language design: the simplicity of substitution versus the expressiveness of mutation. Neither is wrong; both have their place.

---

## Chapter 4: Everything is Procedures

### Introduction

We've seen where substitution breaks. Now let's see how far it goes. This chapter returns to the substitution model and pushes it to its logical extreme. Numbers can be represented as procedures. So can booleans. So can pairs and lists. This is Church encoding: the discovery that if data can be built from procedures, then procedures are the only primitive computation requires. It's similar to learning that every logic circuit reduces to NAND gates—a simplification that reveals something fundamental about what we're working with.

### Subsections

1. Numbers as Procedures
2. Increment and Arithmetic
3. Booleans as Procedures
4. Conditionals Without If
5. Pairs and Lists
6. What This Means

### Conclusion

Church encoding isn't practical—no one writes production code with Church numerals. But it reveals something important: the boundary between "data" and "procedures" is not as solid as it seems. Procedures are enough. Everything else is convenience. Understanding this won't change how you write code day to day, but it changes how you see it. The interpreter from Chapter 1, which seemed so minimal, was already complete. It had everything computation needs.
