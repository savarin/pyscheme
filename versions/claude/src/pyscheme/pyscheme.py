"""
PyScheme: A minimal Scheme interpreter with enterprise-grade implementation.

This module implements a subset of Scheme supporting arithmetic operations,
variable definitions, conditionals, lambda functions, and recursion.
"""

from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from functools import wraps

# Type aliases for clarity
Symbol = str
Number = Union[int, float]
Atom = Union[Number, Symbol]
Expression = Union[Atom, Tuple[Any, ...], Callable[..., Any]]
Procedure = Callable[..., Any]


class SchemeError(Exception):
    """Base exception for Scheme interpreter errors."""
    pass


class UndefinedSymbolError(SchemeError):
    """Raised when accessing an undefined symbol."""
    pass


class InvalidExpressionError(SchemeError):
    """Raised when evaluating an invalid expression."""
    pass


class ArityError(SchemeError):
    """Raised when a procedure is called with wrong number of arguments."""
    pass


class Environment:
    """
    Environment for storing variable bindings with lexical scoping.
    
    An environment consists of a dictionary of bindings and an optional
    reference to an enclosing environment for implementing lexical scope.
    """
    
    def __init__(self, bindings: Optional[Dict[Symbol, Any]] = None, 
                 enclosing: Optional['Environment'] = None) -> None:
        """
        Initialize an environment.
        
        Args:
            bindings: Initial variable bindings
            enclosing: Parent environment for lexical scoping
        """
        self.bindings: Dict[Symbol, Any] = bindings or {}
        self.enclosing = enclosing
    
    def define(self, symbol: Symbol, value: Any) -> None:
        """Define a new variable in this environment."""
        self.bindings[symbol] = value
    
    def get(self, symbol: Symbol) -> Any:
        """
        Look up a variable, checking enclosing scopes if needed.
        
        Raises:
            UndefinedSymbolError: If the symbol is not found
        """
        if symbol in self.bindings:
            return self.bindings[symbol]
        elif self.enclosing is not None:
            return self.enclosing.get(symbol)
        else:
            raise UndefinedSymbolError(f"Undefined symbol: '{symbol}'")
    
    def copy(self) -> 'Environment':
        """Create a shallow copy of this environment."""
        return Environment(self.bindings.copy(), self.enclosing)


# Built-in procedures with type checking
def make_binary_op(op: Callable[[Number, Number], Any]) -> Procedure:
    """Create a type-safe binary operation."""
    def binary_procedure(x: Any, y: Any) -> Any:
        if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
            raise TypeError(f"Expected numbers, got {type(x).__name__} and {type(y).__name__}")
        return op(x, y)
    return binary_procedure


def make_memoized(proc: Procedure) -> Procedure:
    """
    Create a memoized version of a procedure.
    
    Only works for procedures that take hashable arguments.
    """
    cache: Dict[Tuple[Any, ...], Any] = {}
    
    @wraps(proc)
    def memoized_procedure(*args: Any) -> Any:
        # Only memoize if all arguments are hashable
        try:
            key = args
            if key in cache:
                return cache[key]
            result = proc(*args)
            cache[key] = result
            return result
        except TypeError:
            # If arguments aren't hashable, just call the procedure
            return proc(*args)
    
    # Add cache access for monitoring
    memoized_procedure.cache = cache  # type: ignore
    return memoized_procedure


def create_global_environment() -> Environment:
    """Create the global environment with built-in procedures."""
    env = Environment({
        "+": make_binary_op(lambda x, y: x + y),
        "*": make_binary_op(lambda x, y: x * y),
        "-": make_binary_op(lambda x, y: x - y),
        "/": make_binary_op(lambda x, y: x / y if y != 0 else (_ for _ in ()).throw(ZeroDivisionError("Division by zero"))),
        "=": make_binary_op(lambda x, y: x == y),
        "<": make_binary_op(lambda x, y: x < y),
        ">": make_binary_op(lambda x, y: x > y),
    })
    
    # Add memoization special form
    def memoize_proc(target: Any) -> Any:
        """Special form to create memoized version of a procedure."""
        if not callable(target):
            raise InvalidExpressionError("memoize expects a procedure")
        return make_memoized(target)
    
    env.define("memoize", memoize_proc)
    
    return env


# Global environment instance
global_env = create_global_environment()


def validate_expression(expression: Any) -> None:
    """
    Validate that an expression is well-formed.
    
    Raises:
        InvalidExpressionError: If the expression is malformed
    """
    if expression is None:
        raise InvalidExpressionError("Expression cannot be None")
    
    if isinstance(expression, tuple):
        for i, elem in enumerate(expression):
            try:
                validate_expression(elem)
            except InvalidExpressionError as e:
                raise InvalidExpressionError(f"Invalid sub-expression at position {i}: {e}")


def evaluate_atom(atom: Atom, env: Environment) -> Any:
    """
    Evaluate an atomic expression (number or symbol).
    
    Args:
        atom: A number or symbol
        env: The environment for symbol lookup
        
    Returns:
        The value of the atom
        
    Raises:
        UndefinedSymbolError: If a symbol is not defined
        InvalidExpressionError: If the atom type is invalid
    """
    if isinstance(atom, (int, float)):
        return atom
    elif isinstance(atom, str):
        try:
            return env.get(atom)
        except UndefinedSymbolError:
            # Provide helpful context about available symbols
            available = list(env.bindings.keys())
            if env.enclosing:
                available.extend(['...parent scope...'])
            raise UndefinedSymbolError(
                f"Undefined symbol: '{atom}'. Available symbols: {available}"
            )
    else:
        raise InvalidExpressionError(f"Invalid atom type: {type(atom).__name__}")


def evaluate_define(args: Tuple[Any, ...], env: Environment) -> None:
    """
    Handle the 'define' special form.
    
    Syntax: (define symbol value)
    
    Args:
        args: The arguments to define (symbol and value expression)
        env: The environment to define the symbol in
        
    Raises:
        ArityError: If wrong number of arguments
        InvalidExpressionError: If symbol is not a string
    """
    if len(args) != 2:
        raise ArityError(f"'define' expects exactly 2 arguments, got {len(args)}")
    
    symbol, value_expr = args
    
    if not isinstance(symbol, str):
        raise InvalidExpressionError(
            f"'define' expects a symbol (string) as first argument, got {type(symbol).__name__}: {symbol}"
        )
    
    if not symbol:
        raise InvalidExpressionError("Symbol name cannot be empty")
    
    if symbol in {'define', 'if', 'lambda'}:
        raise InvalidExpressionError(f"Cannot redefine special form '{symbol}'")
    
    try:
        value = evaluate(value_expr, env)
        env.define(symbol, value)
    except Exception as e:
        raise InvalidExpressionError(f"Error evaluating value for '{symbol}': {e}")
    
    return None


def evaluate_if(args: Tuple[Any, ...], env: Environment) -> Any:
    """
    Handle the 'if' special form.
    
    Syntax: (if condition then-expr else-expr)
    
    Args:
        args: The condition, then, and else expressions
        env: The environment for evaluation
        
    Returns:
        Result of then-expr if condition is truthy, else-expr otherwise
        
    Raises:
        ArityError: If wrong number of arguments
    """
    if len(args) != 3:
        raise ArityError(f"'if' expects exactly 3 arguments, got {len(args)}")
    
    condition_expr, then_expr, else_expr = args
    
    try:
        condition = evaluate(condition_expr, env)
    except Exception as e:
        raise InvalidExpressionError(f"Error evaluating 'if' condition: {e}")
    
    # In Scheme, only #f (false) is falsy, but we'll use Python's truthiness
    if condition:
        return evaluate(then_expr, env)
    else:
        return evaluate(else_expr, env)


def evaluate_lambda(args: Tuple[Any, ...], env: Environment) -> Procedure:
    """
    Handle the 'lambda' special form.
    
    Syntax: (lambda (param1 param2 ...) body)
    
    Args:
        args: The parameter list and body expression
        env: The environment to capture for closure
        
    Returns:
        A callable procedure
        
    Raises:
        ArityError: If wrong number of arguments
        InvalidExpressionError: If parameters are malformed
    """
    if len(args) != 2:
        raise ArityError(f"'lambda' expects exactly 2 arguments, got {len(args)}")
    
    params, body = args
    
    # Validate parameters
    if not isinstance(params, tuple):
        raise InvalidExpressionError(
            f"'lambda' parameters must be a tuple, got {type(params).__name__}"
        )
    
    param_names = []
    for i, p in enumerate(params):
        if not isinstance(p, str):
            raise InvalidExpressionError(
                f"Parameter {i} must be a symbol (string), got {type(p).__name__}: {p}"
            )
        if not p:
            raise InvalidExpressionError(f"Parameter {i} cannot be empty string")
        if p in param_names:
            raise InvalidExpressionError(f"Duplicate parameter name: '{p}'")
        param_names.append(p)
    
    # Validate body
    validate_expression(body)
    
    def procedure(*arguments: Any) -> Any:
        """The created lambda procedure with closure."""
        if len(arguments) != len(params):
            raise ArityError(
                f"Procedure expects {len(params)} argument(s) ({', '.join(params)}), "
                f"got {len(arguments)}"
            )
        
        # Create new environment for this function call
        local_env = Environment(dict(zip(params, arguments)), env)
        
        return evaluate(body, local_env)
    
    # Add metadata for better error messages
    procedure.__name__ = f"<lambda({', '.join(params)})>"
    
    return procedure


def evaluate_application(operator: Any, operands: Tuple[Any, ...], env: Environment) -> Any:
    """
    Evaluate a procedure application.
    
    Args:
        operator: The procedure or expression that evaluates to a procedure
        operands: The argument expressions
        env: The environment for evaluation
        
    Returns:
        The result of applying the procedure to the evaluated arguments
        
    Raises:
        InvalidExpressionError: If operator is not callable
        ArityError: If wrong number of arguments
    """
    try:
        proc = evaluate(operator, env)
    except Exception as e:
        raise InvalidExpressionError(f"Error evaluating operator '{operator}': {e}")
    
    if not callable(proc):
        raise InvalidExpressionError(
            f"Cannot apply non-procedure: {operator} evaluates to {type(proc).__name__}"
        )
    
    # Evaluate all arguments
    args = []
    for i, operand in enumerate(operands):
        try:
            args.append(evaluate(operand, env))
        except Exception as e:
            raise InvalidExpressionError(f"Error evaluating argument {i}: {e}")
    
    # Apply the procedure
    try:
        return proc(*args)
    except ArityError:
        # Re-raise ArityError with procedure context
        proc_name = getattr(proc, '__name__', str(operator))
        raise ArityError(f"Wrong number of arguments for {proc_name}")
    except TypeError as e:
        if "arguments" in str(e):
            proc_name = getattr(proc, '__name__', str(operator))
            raise ArityError(f"Wrong number of arguments for {proc_name}: {e}")
        raise InvalidExpressionError(f"Error applying procedure: {e}")
    except Exception as e:
        raise InvalidExpressionError(f"Error during procedure application: {e}")


def evaluate(expression: Expression, env: Optional[Environment] = None) -> Any:
    """
    Evaluate a Scheme expression in the given environment.
    
    Args:
        expression: A Scheme expression (atom, list, or callable)
        env: The environment for variable lookup (defaults to global environment)
        
    Returns:
        The result of evaluating the expression
        
    Raises:
        UndefinedSymbolError: If a symbol is not defined
        InvalidExpressionError: If the expression is malformed
        ArityError: If a procedure is called with wrong number of arguments
    """
    if env is None:
        env = global_env
    
    # Handle callable objects (procedures)
    if callable(expression):
        return expression
    
    # Handle atoms
    if not isinstance(expression, tuple):
        return evaluate_atom(expression, env)
    
    # Handle empty expression
    if not expression:
        raise InvalidExpressionError("Cannot evaluate empty expression")
    
    # Handle special forms and applications
    operator = expression[0]
    args = expression[1:]
    
    # Special forms
    if operator == "define":
        return evaluate_define(args, env)
    elif operator == "if":
        return evaluate_if(args, env)
    elif operator == "lambda":
        return evaluate_lambda(args, env)
    else:
        # Regular procedure application
        return evaluate_application(operator, args, env)


# Maintain backward compatibility
definitions = global_env.bindings
