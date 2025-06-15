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
