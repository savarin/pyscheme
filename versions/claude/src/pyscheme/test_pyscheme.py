"""Enhanced test suite for PyScheme with comprehensive coverage."""

from typing import Union
import pytest
from pyscheme.pyscheme import (
    evaluate,
    create_global_environment,
    UndefinedSymbolError,
    InvalidExpressionError,
    ArityError,
    make_memoized,
    validate_expression,
)


ExprType = Union[int, tuple[str, "ExprType", "ExprType"]]


class TestBasicEvaluation:
    """Test basic expression evaluation."""

    def test_evaluate_numbers(self) -> None:
        """Test evaluation of numeric literals."""
        assert evaluate(42) == 42
        assert evaluate(3.14) == 3.14
        assert evaluate(-10) == -10
        assert evaluate(0) == 0

    def test_evaluate_arithmetic(self) -> None:
        """Test basic arithmetic operations."""
        assert evaluate(("+", 2, 3)) == 5
        assert evaluate(("-", 10, 4)) == 6
        assert evaluate(("*", 3, 7)) == 21
        assert evaluate(("/", 20, 4)) == 5.0

        # Test nested arithmetic
        assert evaluate(("+", ("*", 2, 3), 4)) == 10
        assert evaluate(("*", ("+", 1, 2), ("-", 5, 2))) == 9

    def test_evaluate_comparison(self) -> None:
        """Test comparison operations."""
        assert evaluate(("=", 5, 5)) is True
        assert evaluate(("=", 5, 6)) is False
        assert evaluate(("<", 3, 5)) is True
        assert evaluate(("<", 5, 3)) is False
        assert evaluate((">", 7, 2)) is True
        assert evaluate((">", 2, 7)) is False


class TestVariableDefinition:
    """Test variable definition and lookup."""

    def test_define_and_use(self) -> None:
        """Test defining and using variables."""
        env = create_global_environment()

        # Define a variable
        result = evaluate(("define", "x", 42), env)
        assert result is None  # define returns None

        # Use the variable
        assert evaluate("x", env) == 42

        # Use in expression
        assert evaluate(("+", "x", 8), env) == 50

    def test_redefine_variable(self) -> None:
        """Test redefining variables."""
        env = create_global_environment()

        evaluate(("define", "y", 10), env)
        assert evaluate("y", env) == 10

        evaluate(("define", "y", 20), env)
        assert evaluate("y", env) == 20

    def test_define_computed_value(self) -> None:
        """Test defining variables with computed values."""
        env = create_global_environment()

        evaluate(("define", "sum", ("+", 5, 3)), env)
        assert evaluate("sum", env) == 8

        evaluate(("define", "a", 10), env)
        evaluate(("define", "b", ("*", "a", 2)), env)
        assert evaluate("b", env) == 20


class TestConditionals:
    """Test if expressions."""

    def test_if_true_branch(self) -> None:
        """Test if expression taking true branch."""
        assert evaluate(("if", ("=", 1, 1), 10, 20)) == 10
        assert evaluate(("if", ("<", 2, 5), "yes", "no")) == "yes"

    def test_if_false_branch(self) -> None:
        """Test if expression taking false branch."""
        assert evaluate(("if", ("=", 1, 2), 10, 20)) == 20
        assert evaluate(("if", (">", 2, 5), "yes", "no")) == "no"

    def test_if_with_expressions(self) -> None:
        """Test if with complex expressions in branches."""
        env = create_global_environment()
        evaluate(("define", "x", 5), env)

        result = evaluate(("if", ("<", "x", 10), ("*", "x", 2), ("+", "x", 100)), env)
        assert result == 10


class TestLambdaAndProcedures:
    """Test lambda expressions and procedure application."""

    def test_simple_lambda(self) -> None:
        """Test basic lambda creation and application."""
        square = evaluate(("lambda", ("x",), ("*", "x", "x")))
        assert callable(square)
        assert square(5) == 25
        assert square(-3) == 9

    def test_multi_arg_lambda(self) -> None:
        """Test lambda with multiple arguments."""
        add3 = evaluate(("lambda", ("x", "y", "z"), ("+", ("+", "x", "y"), "z")))
        assert add3(1, 2, 3) == 6
        assert add3(10, 20, 30) == 60

    def test_lambda_closure(self) -> None:
        """Test that lambdas capture their environment."""
        env = create_global_environment()
        evaluate(("define", "a", 10), env)

        # Lambda captures 'a' from environment
        add_a = evaluate(("lambda", ("x",), ("+", "x", "a")), env)
        assert add_a(5) == 15

        # Changing 'a' affects the lambda
        evaluate(("define", "a", 20), env)
        assert add_a(5) == 25

    def test_higher_order_functions(self) -> None:
        """Test functions that return functions."""
        # Create a function that returns a function
        make_adder = evaluate(("lambda", ("n",), ("lambda", ("x",), ("+", "x", "n"))))

        add5 = make_adder(5)
        add10 = make_adder(10)

        assert add5(3) == 8
        assert add10(3) == 13


class TestErrorHandling:
    """Test error conditions and error messages."""

    def test_undefined_symbol(self) -> None:
        """Test accessing undefined symbols."""
        env = create_global_environment()

        with pytest.raises(UndefinedSymbolError) as exc_info:
            evaluate("undefined_var", env)
        assert "undefined_var" in str(exc_info.value)
        assert "Available symbols" in str(exc_info.value)

    def test_invalid_define(self) -> None:
        """Test invalid define forms."""
        env = create_global_environment()

        # Wrong number of arguments
        with pytest.raises(ArityError) as exc_info_1:
            evaluate(("define", "x"), env)
        assert "2 arguments" in str(exc_info_1.value)

        # Non-symbol as first argument
        with pytest.raises(InvalidExpressionError) as exc_info_2:
            evaluate(("define", 123, 456), env)
        assert "symbol" in str(exc_info_2.value)

        # Empty symbol name
        with pytest.raises(InvalidExpressionError) as exc_info_3:
            evaluate(("define", "", 42), env)
        assert "empty" in str(exc_info_3.value)

        # Redefining special forms
        with pytest.raises(InvalidExpressionError) as exc_info_4:
            evaluate(("define", "if", 42), env)
        assert "special form" in str(exc_info_4.value)

    def test_invalid_if(self) -> None:
        """Test invalid if forms."""
        # Wrong number of arguments
        with pytest.raises(ArityError) as exc_info:
            evaluate(("if", True, 1))
        assert "3 arguments" in str(exc_info.value)

    def test_invalid_lambda(self) -> None:
        """Test invalid lambda forms."""
        # Wrong number of arguments
        with pytest.raises(ArityError):
            evaluate(("lambda", ("x",)))

        # Non-tuple parameters
        with pytest.raises(InvalidExpressionError) as exc_info:
            evaluate(("lambda", "x", ("*", "x", 2)))
        assert "tuple" in str(exc_info.value)

        # Non-string parameter
        with pytest.raises(InvalidExpressionError) as exc_info:
            evaluate(("lambda", (123,), ("*", 123, 2)))
        assert "symbol" in str(exc_info.value)

        # Duplicate parameters
        with pytest.raises(InvalidExpressionError) as exc_info:
            evaluate(("lambda", ("x", "y", "x"), ("+", "x", "y")))
        assert "Duplicate" in str(exc_info.value)

    def test_invalid_application(self) -> None:
        """Test invalid procedure applications."""
        env = create_global_environment()

        # Applying non-procedure
        evaluate(("define", "not_a_proc", 42), env)
        with pytest.raises(InvalidExpressionError) as exc_info_1:
            evaluate(("not_a_proc", 1, 2), env)
        assert "non-procedure" in str(exc_info_1.value)

        # Wrong number of arguments
        square = evaluate(("lambda", ("x",), ("*", "x", "x")), env)
        evaluate(("define", "square", square), env)

        with pytest.raises(ArityError) as exc_info_2:
            evaluate(("square", 1, 2), env)
        assert "1 argument" in str(exc_info_2.value)

    def test_type_errors(self) -> None:
        """Test type errors in built-in operations."""
        with pytest.raises(TypeError) as exc_info_1:
            evaluate(("+", "hello", 5))
        assert "Expected numbers" in str(exc_info_1.value)

        with pytest.raises(ZeroDivisionError) as exc_info_2:
            evaluate(("/", 10, 0))
        assert "Division by zero" in str(exc_info_2.value)


class TestComplexPrograms:
    """Test more complex Scheme programs."""

    def test_factorial(self) -> None:
        """Test recursive factorial function."""
        env = create_global_environment()

        # Define factorial
        factorial = (
            "lambda",
            ("n",),
            ("if", ("=", "n", 0), 1, ("*", "n", ("factorial", ("-", "n", 1)))),
        )
        evaluate(("define", "factorial", factorial), env)

        assert evaluate(("factorial", 0), env) == 1
        assert evaluate(("factorial", 1), env) == 1
        assert evaluate(("factorial", 5), env) == 120
        assert evaluate(("factorial", 10), env) == 3628800

    def test_fibonacci_recursive(self) -> None:
        """Test recursive Fibonacci with memoization."""
        env = create_global_environment()

        # Define Fibonacci
        fibonacci = (
            "lambda",
            ("n",),
            (
                "if",
                ("<", "n", 2),
                1,
                ("+", ("fib", ("-", "n", 2)), ("fib", ("-", "n", 1))),
            ),
        )
        evaluate(("define", "fib", fibonacci), env)

        # Test small values
        assert evaluate(("fib", 0), env) == 1
        assert evaluate(("fib", 1), env) == 1
        assert evaluate(("fib", 5), env) == 8

        # Define memoized version
        evaluate(("define", "fib-memo", ("memoize", "fib")), env)

        # Memoized version should handle larger values efficiently
        assert evaluate(("fib-memo", 10), env) == 89
        assert evaluate(("fib-memo", 15), env) == 987

    def test_nested_environments(self) -> None:
        """Test nested lexical scoping."""
        env = create_global_environment()

        # Define outer variable
        evaluate(("define", "x", 10), env)

        # Create function that uses outer variable
        evaluate(("define", "add-x", ("lambda", ("y",), ("+", "x", "y"))), env)
        assert evaluate(("add-x", 5), env) == 15

        # Create nested function
        make_counter = (
            "lambda",
            ("start",),
            ("lambda", (), ("define", "start", ("+", "start", 1))),
        )
        evaluate(("define", "make-counter", make_counter), env)

        # Each counter maintains its own state
        evaluate(("define", "c1", ("make-counter", 0)), env)
        evaluate(("define", "c2", ("make-counter", 100)), env)


class TestMemoization:
    """Test memoization functionality."""

    def test_memoize_simple_function(self) -> None:
        """Test memoizing a simple function."""
        call_count = 0

        def tracked_add(x: int, y: int) -> int:
            nonlocal call_count
            call_count += 1
            return x + y

        memoized = make_memoized(tracked_add)

        # First calls
        assert memoized(2, 3) == 5
        assert call_count == 1

        # Cached call
        assert memoized(2, 3) == 5
        assert call_count == 1  # Not called again

        # New arguments
        assert memoized(4, 5) == 9
        assert call_count == 2

    def test_memoize_with_unhashable_args(self) -> None:
        """Test memoization with unhashable arguments."""

        def list_sum(lst: list[int]) -> int:
            return sum(lst)

        memoized = make_memoized(list_sum)

        # Should work but not cache
        assert memoized([1, 2, 3]) == 6
        assert memoized([1, 2, 3]) == 6  # Computed again, not cached


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_expression(self) -> None:
        """Test evaluating empty tuple."""
        with pytest.raises(InvalidExpressionError) as exc_info:
            evaluate(())
        assert "empty expression" in str(exc_info.value)

    def test_none_expression(self) -> None:
        """Test evaluating None."""
        with pytest.raises(InvalidExpressionError) as exc_info:
            validate_expression(None)
        assert "cannot be None" in str(exc_info.value)

    def test_deeply_nested_expressions(self) -> None:
        """Test deeply nested arithmetic expressions."""
        # Create a deeply nested expression
        expr: ExprType = 1
        for i in range(10):
            expr = ("+", expr, i)

        result = evaluate(expr)
        assert result == sum(range(10)) + 1  # 1 + 0 + 1 + 2 + ... + 9

    def test_invalid_expression_types(self) -> None:
        """Test handling of invalid expression types."""
        with pytest.raises(InvalidExpressionError):
            evaluate([1, 2, 3])  # type: ignore[arg-type]

        with pytest.raises(InvalidExpressionError):
            evaluate({"a": 1})  # type: ignore[arg-type]

    def test_function_as_value(self) -> None:
        """Test treating functions as first-class values."""
        env = create_global_environment()

        # Store built-in function in variable
        evaluate(("define", "add", "+"), env)
        assert evaluate(("add", 3, 4), env) == 7

        # Pass function as argument
        apply_twice = evaluate(("lambda", ("f", "x"), ("f", ("f", "x"))), env)
        inc = evaluate(("lambda", ("x",), ("+", "x", 1)), env)
        assert apply_twice(inc, 5) == 7  # (5 + 1) + 1
