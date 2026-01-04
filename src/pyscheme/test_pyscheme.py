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
    Fibonacci sequence using pure lambda calculus constructs.

    This demonstrates that Fibonacci can be computed using only lambda
    abstractions - no built-in if, no built-in arithmetic, just procedures.

    The approach:
    1. Church numerals represent numbers as repeated function application
    2. Church pairs hold two values (used for iteration state)
    3. The fib_step function transforms (a, b) -> (b, a+b)
    4. Apply fib_step n times to (0, 1) and extract the first element

    This is the iterative approach to Fibonacci, which is elegant in lambda
    calculus because it avoids the need for the Y combinator.
    """
    # fmt: off

    # === Church Numerals ===
    # A Church numeral n is a function that applies f to x, n times.
    # zero: λf.λx.x (apply f zero times, just return x)
    zero = (
        "lambda", ("f",),
        (
            "lambda", ("x",), "x",
        )
    )

    # increment: λn.λf.λx.f((n f) x)
    # Takes a numeral n and returns n+1 by applying f one more time
    increment = (
        "lambda", ("n",),
        (
            "lambda", ("f",),
            (
                "lambda", ("x",), ("f", (("n", "f"), "x")),
            )
        )
    )

    # === Church Pairs (matching test_pair style) ===
    # cons takes two arguments: λx,y.λm.(m x y)
    cons = (
        "lambda", ("x", "y"),
        (
            "lambda", ("m",), ("m", "x", "y"),
        )
    )

    # car: λz.z(λp,q.p) - selects the first element
    car = (
        "lambda", ("z",),
        (
            "z", ("lambda", ("p", "q"), "p"),
        )
    )

    # cdr: λz.z(λp,q.q) - selects the second element
    cdr = (
        "lambda", ("z",),
        (
            "z", ("lambda", ("p", "q"), "q"),
        )
    )

    # === Church Addition ===
    # add: λm.λn.λf.λx.(m f)((n f) x)
    # Applies f m times, then n times
    add = (
        "lambda", ("m", "n"),
        (
            "lambda", ("f",),
            (
                "lambda", ("x",), (("m", "f"), (("n", "f"), "x")),
            )
        )
    )

    # === Fibonacci Step ===
    # fib_step: λp.cons (cdr p) (add (car p) (cdr p))
    # Transforms (a, b) -> (b, a+b)
    fib_step = (
        "lambda", ("p",),
        (
            "cons",
            ("cdr", "p"),
            ("add", ("car", "p"), ("cdr", "p")),
        )
    )

    # === Fibonacci Function ===
    # The initial pair for Fibonacci: (fib(0), fib(1)) = (0, 1)
    # After n applications of fib_step:
    # n=0: (0, 1) -> car = 0
    # n=1: (1, 1) -> car = 1
    # n=2: (1, 2) -> car = 1
    # n=3: (2, 3) -> car = 2
    # n=4: (3, 5) -> car = 3
    # n=5: (5, 8) -> car = 5
    # So fib(n) = car(n fib_step (cons zero one))

    # We need 'one' for the initial pair
    one = ("increment", "zero")

    # fib: λn.car((n fib_step) (cons zero one))
    fib = (
        "lambda", ("n",),
        (
            "car",
            (("n", "fib_step"), ("cons", "zero", "one")),
        )
    )
    # fmt: on

    # Define all the lambda calculus constructs
    evaluate(("define", "zero", zero))
    evaluate(("define", "increment", increment))
    evaluate(("define", "cons", cons))
    evaluate(("define", "car", car))
    evaluate(("define", "cdr", cdr))
    evaluate(("define", "add", add))
    evaluate(("define", "fib_step", fib_step))
    evaluate(("define", "one", one))
    evaluate(("define", "fib", fib))

    # Helper to convert Church numeral to Python integer
    # We apply the numeral to (+1) and 0
    def church_to_int(church_numeral):
        return evaluate(((church_numeral, ("lambda", ("x",), ("+", "x", 1))), 0))

    # Build Church numerals for testing
    two = ("increment", "one")
    three = ("increment", two)
    four = ("increment", three)
    five = ("increment", four)
    six = ("increment", five)
    seven = ("increment", six)
    eight = ("increment", seven)
    nine = ("increment", eight)
    ten = ("increment", nine)

    # Test Fibonacci sequence: 0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55
    assert church_to_int(("fib", "zero")) == 0
    assert church_to_int(("fib", "one")) == 1
    assert church_to_int(("fib", two)) == 1
    assert church_to_int(("fib", three)) == 2
    assert church_to_int(("fib", four)) == 3
    assert church_to_int(("fib", five)) == 5
    assert church_to_int(("fib", six)) == 8
    assert church_to_int(("fib", seven)) == 13
    assert church_to_int(("fib", eight)) == 21
    assert church_to_int(("fib", nine)) == 34
    assert church_to_int(("fib", ten)) == 55
