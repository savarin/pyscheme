# Step 0: Context

This document summarizes the planning discussion for a book based on the pyscheme interpreter and SICP blog post.

---

## Source Material

Two primary sources:

1. **pyscheme.py** (~60 lines) — A minimal Scheme interpreter in Python using substitution
2. **SICP blog post** — "1 week with David Beazley and SICP" describing the learning experience

The interpreter handles: primitives, symbols, define, if, lambda, and procedure application. The tests demonstrate Fibonacci, Church numerals, Church pairs, and Church booleans.

---

## Core Thesis

From the blog post:

> "What did I learn? It's hard to describe. I'll explain by analogy. When I learned about compilers, I discovered that languages have much more in common than I realized; I now see the big picture. With SICP it's a bit like that, but with the idea of computation more generally."

**The book is about:**
- Substitution as a simple, elegant mental model for computation
- How far it goes (Church encoding — everything is procedures)
- Where it breaks (state/mutation)
- What replaces it (environments)

---

## Book Structure

**No parts.** Four chapters is short enough that grouping adds unnecessary hierarchy.

**Chapter order:** Show the full landscape (works, breaks, replacement) before going deep into Church encoding.

| Chapter | Content | Code Coverage |
|---------|---------|---------------|
| 1. The Substitution Model | Build interpreter, prove with Fibonacci | Full (pyscheme.py) |
| 2. Where Substitution Breaks | State, bank account example, why it fails | Conceptual (blog post) |
| 3. The Environment Model | What replaces substitution | Conceptual only — may need new code |
| 4. Everything is Procedures | Church encoding | Full (test_pyscheme.py) |

**Note:** Chapter 3 is conceptual for now. We'll revisit whether it needs working code after seeing how the narrative reads.

---

## Writing Process

| Step | Deliverable | File |
|------|-------------|------|
| 0 | Context | `step-0-context.md` (this file) |
| 1 | Book — back cover blurb | `step-1-book.md` (done) |
| 2 | Chapter structure — intro, conclusion, subsections | `step-2-structure.md` |
| 3 | Actual writing | `chapters/` |

---

## Key Decisions

**Why no parts?**
Four chapters is short enough that the arc is self-evident. Parts would add organizational overhead without benefit.

**Why this chapter ordering?**
Show the full shape of substitution (where it works, where it breaks, what replaces it) before diving deep into Church encoding. This way Church encoding becomes "look how rich the working part is" rather than an unmoored exploration.

**Why keep environments conceptual for now?**
The blog post describes why substitution breaks and what conceptually replaces it, but pyscheme.py has no environment-based code. Writing new code is possible but we want to see how the narrative reads first.

**Voice and tone:**
Neutral teaching voice. Precise, not dramatic. Honest about what the book is and isn't.

**Target audience:**
Recurse Center fellows who want to work through material slowly, with code, discussing one chapter per week.

---

## Files

- `src/pyscheme/pyscheme.py` — The interpreter
- `src/pyscheme/test_pyscheme.py` — Tests including Church encoding
- `docs/sicp/` — The blog post (HTML export)
- `docs/reference/` — Planning documents (this directory)
- `docs/chapters/` — Actual chapter content (to be written)
