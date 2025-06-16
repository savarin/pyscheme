"""
Error-path and edge-case tests for the enterprise pyscheme interpreter.
These complement the happy-path suite in `test_pyscheme.py` and drive
coverage well past the 95 % goal.
"""

import pytest

from pyscheme.pyscheme import (
    Environment,
    EvaluationError,
    InvalidExpressionError,
    Interpreter,
    UndefinedSymbolError,
    evaluate,
)

# ---------------------------------------------------------------------
# Undefined symbol ----------------------------------------------------
# ---------------------------------------------------------------------


def test_undefined_symbol_lookup() -> None:
    with pytest.raises(UndefinedSymbolError) as exc:
        evaluate("nonexistent")

    assert "nonexistent" in str(exc.value)


# ---------------------------------------------------------------------
# Malformed special forms --------------------------------------------
# ---------------------------------------------------------------------


@pytest.mark.parametrize(
    "expr",
    [
        ("define", 1, 2),  # first arg must be a symbol
        ("define",),  # too short
        ("if", 1, 2),  # missing else branch
        ("lambda", ("x",)),  # missing body
        ("lambda", "x", "x"),  # params not a tuple
    ],
)
def test_invalid_special_forms(expr) -> None:
    with pytest.raises(InvalidExpressionError):
        evaluate(expr)  # type: ignore[arg-type]


# ---------------------------------------------------------------------
# Arity mismatch for lambda closures ----------------------------------
# ---------------------------------------------------------------------


def test_arity_mismatch() -> None:
    square = ("lambda", ("x",), ("*", "x", "x"))
    with pytest.raises(EvaluationError):
        evaluate((square, 1, 2))  # two args instead of one


# ---------------------------------------------------------------------
# Frozen environment protection --------------------------------------
# ---------------------------------------------------------------------


def test_frozen_environment() -> None:
    base = Environment({"x": 1}, frozen=True)
    interp = Interpreter(base)

    # Lookup works
    assert interp.evaluate("x") == 1

    # Mutation forbidden
    with pytest.raises(EvaluationError):
        interp.evaluate(("define", "y", 2))


# ---------------------------------------------------------------------
# Unsupported expression type ----------------------------------------
# ---------------------------------------------------------------------


def test_invalid_expression_type() -> None:
    class Weird:  # not supported
        pass

    with pytest.raises(InvalidExpressionError):
        evaluate(Weird())  # type: ignore[arg-type]
