"""
Fibonacci Number Generation using Pure Lambda Calculus

This test demonstrates computing Fibonacci numbers using ONLY lambda calculus
constructs - no built-in arithmetic, no named recursion, just lambdas.

The implementation uses an ITERATIVE approach with pairs:
- Start with pair (fib(0), fib(1)) = (0, 1)
- Transform: (a, b) -> (b, a+b)
- Apply transformation n times
- Extract first element to get fib(n)

This elegant approach avoids the need for Y/Z combinators entirely!

Key concepts:
- Church Numerals: Numbers represented as lambda functions
- Church Booleans: TRUE and FALSE as lambda functions
- Pairs: Constructors and selectors as lambdas
- Iteration via Church numeral application
"""

from pyscheme.pyscheme import evaluate


def test_fibonacci_lambda_calculus():
    """
    Compute Fibonacci numbers using pure lambda calculus.

    This implementation uses:
    - Church numerals for representing numbers
    - Pairs for building the Fibonacci iteration
    - Church numeral iteration (applying a function n times)

    No built-in arithmetic or explicit recursion is used.
    Everything is built from lambda.
    """

    # =========================================================================
    # CHURCH BOOLEANS
    # =========================================================================

    # TRUE = λx.λy.x (returns first argument)
    # fmt: off
    TRUE = (
        "lambda", ("x",),
        (
            "lambda", ("y",), "x",
        )
    )

    # FALSE = λx.λy.y (returns second argument)
    FALSE = (
        "lambda", ("x",),
        (
            "lambda", ("y",), "y",
        )
    )
    # fmt: on

    evaluate(("define", "TRUE", TRUE))
    evaluate(("define", "FALSE", FALSE))

    # =========================================================================
    # PAIRS (the key data structure for iterative Fibonacci)
    # =========================================================================

    # fmt: off
    # CONS = λx.λy.λm.((m x) y) - create a pair
    CONS = (
        "lambda", ("x",),
        (
            "lambda", ("y",),
            (
                "lambda", ("m",), (("m", "x"), "y"),
            )
        )
    )

    # CAR = λz.(z TRUE) - extract first element
    CAR = (
        "lambda", ("z",),
        (
            "z", "TRUE",
        )
    )

    # CDR = λz.(z FALSE) - extract second element
    CDR = (
        "lambda", ("z",),
        (
            "z", "FALSE",
        )
    )
    # fmt: on

    evaluate(("define", "CONS", CONS))
    evaluate(("define", "CAR", CAR))
    evaluate(("define", "CDR", CDR))

    # Verify pairs work
    evaluate(("define", "test_pair", (("CONS", 1), 2)))
    assert evaluate(("CAR", "test_pair")) == 1
    assert evaluate(("CDR", "test_pair")) == 2

    # =========================================================================
    # CHURCH NUMERALS
    # =========================================================================

    # fmt: off
    # ZERO = λf.λx.x - apply f zero times
    ZERO = (
        "lambda", ("f",),
        (
            "lambda", ("x",), "x",
        )
    )

    # ONE = λf.λx.(f x) - apply f once
    ONE = (
        "lambda", ("f",),
        (
            "lambda", ("x",), ("f", "x"),
        )
    )

    # TWO = λf.λx.(f (f x)) - apply f twice
    TWO = (
        "lambda", ("f",),
        (
            "lambda", ("x",), ("f", ("f", "x")),
        )
    )

    # SUCC = λn.λf.λx.(f ((n f) x)) - successor
    SUCC = (
        "lambda", ("n",),
        (
            "lambda", ("f",),
            (
                "lambda", ("x",), ("f", (("n", "f"), "x")),
            )
        )
    )

    # ADD = λm.λn.λf.λx.((m f) ((n f) x)) - addition
    ADD = (
        "lambda", ("m",),
        (
            "lambda", ("n",),
            (
                "lambda", ("f",),
                (
                    "lambda", ("x",), (("m", "f"), (("n", "f"), "x")),
                )
            )
        )
    )
    # fmt: on

    evaluate(("define", "ZERO", ZERO))
    evaluate(("define", "ONE", ONE))
    evaluate(("define", "TWO", TWO))
    evaluate(("define", "SUCC", SUCC))
    evaluate(("define", "ADD", ADD))

    # Helper to convert Church numeral to integer
    # TO_INT = λn.((n (λx.x+1)) 0)
    # fmt: off
    TO_INT = ("lambda", ("n",), (("n", ("lambda", ("x",), ("+", "x", 1))), 0))
    # fmt: on
    evaluate(("define", "TO_INT", TO_INT))

    # Verify Church numerals
    assert evaluate(("TO_INT", "ZERO")) == 0
    assert evaluate(("TO_INT", "ONE")) == 1
    assert evaluate(("TO_INT", "TWO")) == 2
    assert evaluate(("TO_INT", ("SUCC", "TWO"))) == 3

    # =========================================================================
    # FIBONACCI USING ITERATION
    # =========================================================================
    #
    # The key insight: A Church numeral n is a function that applies f to x
    # exactly n times: n = λf.λx.(f (f (f ... (f x))))
    #
    # We use this iteration property to compute Fibonacci:
    # 1. Start with pair (0, 1) representing (fib(0), fib(1))
    # 2. Define FIB_STEP: (a, b) -> (b, a+b)
    # 3. Apply FIB_STEP n times
    # 4. Extract first element
    #
    # This gives us fib(n) without any explicit recursion!

    # fmt: off
    # FIB_STEP = λp.(CONS (CDR p) (ADD (CAR p) (CDR p)))
    # Transforms (a, b) -> (b, a+b)
    FIB_STEP = (
        "lambda", ("p",),
        (
            ("CONS", ("CDR", "p")),
            (("ADD", ("CAR", "p")), ("CDR", "p")),
        )
    )

    # FIB_INIT = (CONS ZERO ONE) = pair (0, 1)
    FIB_INIT = (("CONS", "ZERO"), "ONE")

    # FIB = λn.(CAR ((n FIB_STEP) FIB_INIT))
    # Apply FIB_STEP n times to initial pair, then extract first element
    FIB = (
        "lambda", ("n",),
        (
            "CAR",
            (("n", "FIB_STEP"), "FIB_INIT"),
        )
    )
    # fmt: on

    evaluate(("define", "FIB_STEP", FIB_STEP))
    evaluate(("define", "FIB_INIT", FIB_INIT))
    evaluate(("define", "FIB", FIB))

    # =========================================================================
    # BUILD MORE CHURCH NUMERALS FOR TESTING
    # =========================================================================

    THREE = ("SUCC", "TWO")
    FOUR = ("SUCC", THREE)
    FIVE = ("SUCC", FOUR)
    SIX = ("SUCC", FIVE)
    SEVEN = ("SUCC", SIX)
    EIGHT = ("SUCC", SEVEN)
    NINE = ("SUCC", EIGHT)
    TEN = ("SUCC", NINE)

    evaluate(("define", "THREE", THREE))
    evaluate(("define", "FOUR", FOUR))
    evaluate(("define", "FIVE", FIVE))
    evaluate(("define", "SIX", SIX))
    evaluate(("define", "SEVEN", SEVEN))
    evaluate(("define", "EIGHT", EIGHT))
    evaluate(("define", "NINE", NINE))
    evaluate(("define", "TEN", TEN))

    # =========================================================================
    # TEST THE FIBONACCI SEQUENCE
    # =========================================================================
    # Using pure lambda calculus with Church numerals!
    #
    # The Fibonacci sequence: 0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, ...

    # fib(0) = 0
    result = evaluate(("TO_INT", ("FIB", "ZERO")))
    assert result == 0, f"fib(0) should be 0, got {result}"

    # fib(1) = 1
    result = evaluate(("TO_INT", ("FIB", "ONE")))
    assert result == 1, f"fib(1) should be 1, got {result}"

    # fib(2) = 1
    result = evaluate(("TO_INT", ("FIB", "TWO")))
    assert result == 1, f"fib(2) should be 1, got {result}"

    # fib(3) = 2
    result = evaluate(("TO_INT", ("FIB", "THREE")))
    assert result == 2, f"fib(3) should be 2, got {result}"

    # fib(4) = 3
    result = evaluate(("TO_INT", ("FIB", "FOUR")))
    assert result == 3, f"fib(4) should be 3, got {result}"

    # fib(5) = 5
    result = evaluate(("TO_INT", ("FIB", "FIVE")))
    assert result == 5, f"fib(5) should be 5, got {result}"

    # fib(6) = 8
    result = evaluate(("TO_INT", ("FIB", "SIX")))
    assert result == 8, f"fib(6) should be 8, got {result}"

    # fib(7) = 13
    result = evaluate(("TO_INT", ("FIB", "SEVEN")))
    assert result == 13, f"fib(7) should be 13, got {result}"

    # fib(8) = 21
    result = evaluate(("TO_INT", ("FIB", "EIGHT")))
    assert result == 21, f"fib(8) should be 21, got {result}"

    # fib(9) = 34
    result = evaluate(("TO_INT", ("FIB", "NINE")))
    assert result == 34, f"fib(9) should be 34, got {result}"

    # fib(10) = 55
    result = evaluate(("TO_INT", ("FIB", "TEN")))
    assert result == 55, f"fib(10) should be 55, got {result}"


def test_fibonacci_lambda_components():
    """
    Verify individual components of the lambda calculus Fibonacci.

    This test validates:
    1. Church numeral arithmetic (addition)
    2. Pair operations (cons, car, cdr)
    3. The FIB_STEP transformation
    """

    # Setup Church numerals
    # fmt: off
    ZERO = ("lambda", ("f",), ("lambda", ("x",), "x"))
    ONE = ("lambda", ("f",), ("lambda", ("x",), ("f", "x")))
    TWO = ("lambda", ("f",), ("lambda", ("x",), ("f", ("f", "x"))))
    SUCC = (
        "lambda", ("n",),
        ("lambda", ("f",), ("lambda", ("x",), ("f", (("n", "f"), "x"))))
    )
    ADD = (
        "lambda", ("m",),
        ("lambda", ("n",),
            ("lambda", ("f",),
                ("lambda", ("x",), (("m", "f"), (("n", "f"), "x")))))
    )

    TRUE = ("lambda", ("x",), ("lambda", ("y",), "x"))
    FALSE = ("lambda", ("x",), ("lambda", ("y",), "y"))
    CONS = (
        "lambda", ("x",),
        ("lambda", ("y",), ("lambda", ("m",), (("m", "x"), "y")))
    )
    CAR = ("lambda", ("z",), ("z", "TRUE"))
    CDR = ("lambda", ("z",), ("z", "FALSE"))

    TO_INT = ("lambda", ("n",), (("n", ("lambda", ("x",), ("+", "x", 1))), 0))
    # fmt: on

    evaluate(("define", "ZERO", ZERO))
    evaluate(("define", "ONE", ONE))
    evaluate(("define", "TWO", TWO))
    evaluate(("define", "SUCC", SUCC))
    evaluate(("define", "ADD", ADD))
    evaluate(("define", "TRUE", TRUE))
    evaluate(("define", "FALSE", FALSE))
    evaluate(("define", "CONS", CONS))
    evaluate(("define", "CAR", CAR))
    evaluate(("define", "CDR", CDR))
    evaluate(("define", "TO_INT", TO_INT))

    # Test: Church addition works
    # 2 + 3 = 5
    THREE = ("SUCC", "TWO")
    evaluate(("define", "THREE", THREE))
    result = evaluate(("TO_INT", (("ADD", "TWO"), "THREE")))
    assert result == 5, f"2 + 3 should be 5, got {result}"

    # Test: Pairs with Church numerals work
    # Create pair (2, 3), extract both elements
    pair = (("CONS", "TWO"), "THREE")
    assert evaluate(("TO_INT", ("CAR", pair))) == 2
    assert evaluate(("TO_INT", ("CDR", pair))) == 3

    # Test: FIB_STEP transforms (a, b) -> (b, a+b)
    # fmt: off
    FIB_STEP = (
        "lambda", ("p",),
        (("CONS", ("CDR", "p")), (("ADD", ("CAR", "p")), ("CDR", "p")))
    )
    # fmt: on
    evaluate(("define", "FIB_STEP", FIB_STEP))

    # (0, 1) -> (1, 0+1) = (1, 1)
    pair_0_1 = (("CONS", "ZERO"), "ONE")
    step1 = ("FIB_STEP", pair_0_1)
    assert evaluate(("TO_INT", ("CAR", step1))) == 1
    assert evaluate(("TO_INT", ("CDR", step1))) == 1

    # (1, 1) -> (1, 1+1) = (1, 2)
    pair_1_1 = (("CONS", "ONE"), "ONE")
    step2 = ("FIB_STEP", pair_1_1)
    assert evaluate(("TO_INT", ("CAR", step2))) == 1
    assert evaluate(("TO_INT", ("CDR", step2))) == 2

    # (1, 2) -> (2, 1+2) = (2, 3)
    pair_1_2 = (("CONS", "ONE"), "TWO")
    step3 = ("FIB_STEP", pair_1_2)
    assert evaluate(("TO_INT", ("CAR", step3))) == 2
    assert evaluate(("TO_INT", ("CDR", step3))) == 3


if __name__ == "__main__":
    test_fibonacci_lambda_components()
    print("Component tests passed!")

    test_fibonacci_lambda_calculus()
    print("All Fibonacci lambda calculus tests passed!")
