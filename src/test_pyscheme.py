from pyscheme import evaluate


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
    fibonacci = (
        "lambda", ("n",),
        (
            "if", ("<", "n", 2),
                1,
                ("+", ("fibonacci", ("-", "n", 2)), ("fibonacci", ("-", "n", 1))),
        ),
    )

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
