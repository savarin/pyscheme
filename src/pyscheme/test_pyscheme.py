from pyscheme.pyscheme import evaluate


def test_evaluate():
    assert evaluate(1) == 1

    assert evaluate(("+", 2, 3)) == 5

    evaluate(("define", "x", 2))
    assert evaluate(("+", "x", 3)) == 5

    assert evaluate(("if", ("=", 1, 1), 2, 3)) == 2
    assert evaluate(("if", ("=", 0, 1), 2, 3)) == 3

    assert evaluate((("lambda", ("x",), ("*", "x", "x")), 3)) == 9

    evaluate(("define", "square", ("lambda", ("x",), ("*", "x", "x"))))
    assert evaluate(("square", 3)) == 9


def test_fibonacci():
    # fmt: off
    fibonacci = (
        "lambda", ("n",),
        (
            "if", ("<", "n", 2),
                1,
                ("+", ("fibonacci", ("-", "n", 2)), ("fibonacci", ("-", "n", 1))),
        ),
    )
    # fmt: on

    evaluate(("define", "fibonacci", fibonacci))

    assert evaluate(("fibonacci", 0)) == 1
    assert evaluate(("fibonacci", 1)) == 1
    assert evaluate(("fibonacci", 2)) == 2
    assert evaluate(("fibonacci", 3)) == 3
    assert evaluate(("fibonacci", 4)) == 5
    assert evaluate(("fibonacci", 5)) == 8
    assert evaluate(("fibonacci", 6)) == 13
    assert evaluate(("fibonacci", 7)) == 21
    assert evaluate(("fibonacci", 8)) == 34
    assert evaluate(("fibonacci", 9)) == 55


def test_numerals():
    # fmt: off
    zero = (
        "lambda", ("f",),
        (
            "lambda", ("x",), "x",
        )
    )

    increment = (
        "lambda", ("n",),
        (
            "lambda", ("f",),
            (
                "lambda", ("x",), ("f", (("n", "f"), "x")),
            )
        )
    )

    one = (
        "lambda", ("f",),
        (
            "lambda", ("x",), ("f", "x"),
        )
    )

    two = (
        "lambda", ("f",),
        (
            "lambda", ("x",), ("f", ("f", "x")),
        )
    )
    # fmt: on

    evaluate(("define", "zero", zero))
    evaluate(("define", "increment", increment))

    assert evaluate((("zero", ("lambda", ("x",), ("+", "x", 1))), 0)) == 0
    assert (
        evaluate(((("increment", "zero"), ("lambda", ("x",), ("+", "x", 1))), 0)) == 1
    )

    evaluate(("define", "one", one))
    evaluate(("define", "two", two))

    assert evaluate((("one", ("lambda", ("x",), ("+", "x", 1))), 0)) == 1
    assert evaluate((("two", ("lambda", ("x",), ("+", "x", 1))), 0)) == 2


def test_pair():
    # fmt: off
    cons = (
        "lambda", ("x", "y"),
        (
            "lambda", ("m",), ("m", "x", "y"),
        )
    )

    car = (
        "lambda", ("z"),
        (
            "z", ("lambda", ("p", "q"), "p"),
        )
    )

    cdr = (
        "lambda", ("z"),
        (
            "z", ("lambda", ("p", "q"), "q"),
        )
    )
    # fmt: on

    evaluate(("define", "cons", cons))
    evaluate(("define", "car", car))
    evaluate(("define", "cdr", cdr))

    assert evaluate(("car", ("cons", 1, 2))) == 1
    assert evaluate(("cdr", ("cons", 1, 2))) == 2


def test_if():
    # fmt: off
    true = (
        "lambda", ("x",),
        (
            "lambda", ("y",), "x",
        )
    )

    false = (
        "lambda", ("x",),
        (
            "lambda", ("y",), "y",
        )
    )

    if_procedure = (
        "lambda", ("f",),
        (
            "lambda", ("a",),
            (
                "lambda", ("b",), (("f", "a"), "b"),
            )
        )
    )
    # fmt: on

    evaluate(("define", "true", true))
    evaluate(("define", "false", false))
    evaluate(("define", "if_procedure", if_procedure))

    assert evaluate(((("if_procedure", "true"), 2), 3)) == 2
    assert evaluate(((("if_procedure", "false"), 2), 3)) == 3


def test_fibonacci_lambda_calculus():
    """
    Compute Fibonacci numbers using pure lambda calculus.

    This demonstrates computing Fibonacci using ONLY lambda calculus constructs:
    - Church numerals for representing numbers
    - Pairs (cons/car/cdr) for state
    - Church numeral iteration (no explicit recursion)

    The algorithm:
    1. Start with pair (fib(0), fib(1)) = (0, 1)
    2. Apply FIB_STEP: (a, b) -> (b, a+b) n times
    3. Extract first element to get fib(n)
    """

    # Church booleans for pair selectors
    # fmt: off
    TRUE = ("lambda", ("x",), ("lambda", ("y",), "x"))
    FALSE = ("lambda", ("x",), ("lambda", ("y",), "y"))

    # Pairs using Church encoding
    CONS = (
        "lambda", ("x",),
        ("lambda", ("y",), ("lambda", ("m",), (("m", "x"), "y")))
    )
    CAR = ("lambda", ("z",), ("z", "TRUE"))
    CDR = ("lambda", ("z",), ("z", "FALSE"))

    # Church numerals
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

    # Fibonacci using iterative pair transformation
    # FIB_STEP: (a, b) -> (b, a+b)
    FIB_STEP = (
        "lambda", ("p",),
        (("CONS", ("CDR", "p")), (("ADD", ("CAR", "p")), ("CDR", "p")))
    )
    FIB_INIT = (("CONS", "ZERO"), "ONE")
    FIB = ("lambda", ("n",), ("CAR", (("n", "FIB_STEP"), "FIB_INIT")))

    # Conversion helper (only for testing assertions)
    TO_INT = ("lambda", ("n",), (("n", ("lambda", ("x",), ("+", "x", 1))), 0))
    # fmt: on

    # Define all primitives
    evaluate(("define", "TRUE", TRUE))
    evaluate(("define", "FALSE", FALSE))
    evaluate(("define", "CONS", CONS))
    evaluate(("define", "CAR", CAR))
    evaluate(("define", "CDR", CDR))
    evaluate(("define", "ZERO", ZERO))
    evaluate(("define", "ONE", ONE))
    evaluate(("define", "TWO", TWO))
    evaluate(("define", "SUCC", SUCC))
    evaluate(("define", "ADD", ADD))
    evaluate(("define", "FIB_STEP", FIB_STEP))
    evaluate(("define", "FIB_INIT", FIB_INIT))
    evaluate(("define", "FIB", FIB))
    evaluate(("define", "TO_INT", TO_INT))

    # Build Church numerals for testing
    THREE = ("SUCC", "TWO")
    FOUR = ("SUCC", THREE)
    FIVE = ("SUCC", FOUR)
    SIX = ("SUCC", FIVE)
    SEVEN = ("SUCC", SIX)
    EIGHT = ("SUCC", SEVEN)
    NINE = ("SUCC", EIGHT)
    TEN = ("SUCC", NINE)

    # Test Fibonacci sequence: 0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55
    assert evaluate(("TO_INT", ("FIB", "ZERO"))) == 0
    assert evaluate(("TO_INT", ("FIB", "ONE"))) == 1
    assert evaluate(("TO_INT", ("FIB", "TWO"))) == 1
    assert evaluate(("TO_INT", ("FIB", THREE))) == 2
    assert evaluate(("TO_INT", ("FIB", FOUR))) == 3
    assert evaluate(("TO_INT", ("FIB", FIVE))) == 5
    assert evaluate(("TO_INT", ("FIB", SIX))) == 8
    assert evaluate(("TO_INT", ("FIB", SEVEN))) == 13
    assert evaluate(("TO_INT", ("FIB", EIGHT))) == 21
    assert evaluate(("TO_INT", ("FIB", NINE))) == 34
    assert evaluate(("TO_INT", ("FIB", TEN))) == 55
