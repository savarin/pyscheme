# Step 1: Book (Back Cover)

---

Most programmers have a rough mental model of how code executes. Variables get stored somewhere. Functions do something with their arguments. The runtime handles it. This book offers a more precise model—one simple enough to hold in your head, yet powerful enough to execute real programs by hand.

The model is called substitution. When you call a function, you replace the parameters with arguments in the body, then evaluate the result. When you encounter a variable, you replace it with its value. When you hit a conditional, you pick one branch and discard the other. That's the whole mechanism: symbols replacing symbols, recursively, until you reach a value.

This sounds too simple to be useful. But a working interpreter built entirely on substitution fits in sixty lines of Python. It handles variables, conditionals, recursion, higher-order functions—enough to compute Fibonacci numbers, enough to trace any expression step by step on paper.

The model goes further than you'd expect. Numbers can be represented as functions. So can booleans. So can pairs and lists. This is Church encoding: the discovery that if data can be built from procedures, then procedures are the only primitive you need. It's similar to learning that every logic circuit, no matter how complex, reduces to combinations of NAND gates. A simplification like this isn't just elegant—it reveals something fundamental about what computation is.

The model also breaks. The moment you need a value to change over time—a counter that increments, a balance that decreases—substitution fails. It can't distinguish "the balance before the withdrawal" from "the balance after." To handle mutation, you need something more: environments, scope, the machinery that real interpreters use. Understanding exactly where substitution fails, and what replaces it, explains much of the complexity you encounter in real programming languages.

This book is designed to be worked through, not skimmed. Each chapter has code to run, modify, and break. The ideas are simple to state but take time to absorb—time spent tracing evaluations by hand, implementing Church numerals yourself, sitting with the question of why state complicates everything. If you want to understand computation at a level deeper than syntax and frameworks, this is a place to start.

---

**What you'll need:** Comfort with one programming language. No Scheme experience required—we build the interpreter in Python.

**What this isn't:** A guide to building production interpreters. There's no parsing, no optimization, no error handling. The goal is understanding, not tooling.
