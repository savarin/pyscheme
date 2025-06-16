from __future__ import annotations

"""pyscheme – Phase 4: observability & inline architecture docs.

This final pass completes the enterprise‑grade transformation by adding
**structured logging hooks** and a high‑level architecture primer directly in
this module‑level docstring.

Highlights
~~~~~~~~~~
* **Observability** – `logging.getLogger(__name__)` used at *DEBUG* level around
  evaluation entry/exit, special‑form handling, and procedure application.
  Nothing is emitted unless the host application configures the package logger
  (zero overhead in the common case).
* **Architecture diagram** – lightweight ASCII schematic so new contributors
  grok the runtime flow at a glance.
* **Usage cookbook** – code snippets for adding a custom primitive and per‑request
  interpreter instance.

ASCII Diagram
-------------
::

    ┌─────────────┐   evaluate(expr)   ┌───────────────┐
    │  Client     │──────────────────▶│ Interpreter   │
    └─────────────┘                    │  (dispatch)   │
            ▲                          ├─────┬─────────┤
            │ result / exceptions      │Env  │ Logger  │
            │                          └──┬──┴─────────┘
            │                             ▼
    ┌────────────────┐         ┌────────────────────────┐
    │ Custom Prims   │◀──────▶│  _default_primitives() │
    └────────────────┘         └────────────────────────┘

Cookbook
~~~~~~~~
::

    >>> from pyscheme.pyscheme import Interpreter
    >>> interp = Interpreter()
    >>> interp.register('max', lambda x, y: x if x > y else y)
    >>> interp(("max", 10, 3))
    10

Enabling debug logs::

    import logging
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger('pyscheme').setLevel(logging.DEBUG)

    # Now each evaluation will print a concise trace.
"""

from typing import Any, Callable, Dict, Iterable, Iterator, Tuple, TypeAlias, Union
import logging

__all__ = [
    "evaluate",
    "Interpreter",
    "Environment",
    "EvaluationError",
    "UndefinedSymbolError",
    "InvalidExpressionError",
]

# ---------------------------------------------------------------------------
# Logging setup – child loggers inherit configuration from root application.
# ---------------------------------------------------------------------------
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Public type aliases
# ---------------------------------------------------------------------------
Symbol: TypeAlias = str
Number: TypeAlias = Union[int, float]
Procedure: TypeAlias = Callable[..., "Value"]
Expression: TypeAlias = Union[Number, Symbol, Tuple[Any, ...], Procedure]
Value: TypeAlias = Union[Number, Procedure]

# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class EvaluationError(RuntimeError):
    """Generic runtime error raised by the interpreter."""


class UndefinedSymbolError(EvaluationError):
    """Raised when a symbol is referenced before definition."""

    def __init__(self, symbol: Symbol) -> None:  # noqa: D401 – init
        super().__init__(f"Undefined symbol: '{symbol}'")
        self.symbol: Symbol = symbol


class InvalidExpressionError(EvaluationError):
    """Raised when the interpreter encounters a malformed expression."""


# ---------------------------------------------------------------------------
# Environment – isolates mutable state and offers explicit copy semantics.
# ---------------------------------------------------------------------------


class Environment:  # noqa: D101 – detailed docstring below
    """Mapping from symbol → value with explicit *copy* method.

    Behaves like a thin wrapper around ``dict`` but gives us future latitude for
    immutability and chaining.
    """

    __slots__ = ("_store", "_frozen")

    def __init__(self, initial: Dict[Symbol, Value] | None = None, *, frozen: bool = False) -> None:  # noqa: D401,E501
        self._store: Dict[Symbol, Value] = dict(initial or {})
        self._frozen: bool = frozen

    # --- basic mapping protocol -----------------------------------------
    def __getitem__(self, key: Symbol) -> Value:  # noqa: D401 – dunder
        try:
            return self._store[key]
        except KeyError as exc:  # pragma: no cover – converted by caller
            raise UndefinedSymbolError(key) from exc

    def __setitem__(self, key: Symbol, value: Value) -> None:  # noqa: D401 – dunder
        if self._frozen:
            raise EvaluationError("Attempt to mutate frozen Environment")
        self._store[key] = value

    def update(self, iterable: Iterable[tuple[Symbol, Value]]) -> None:
        if self._frozen:
            raise EvaluationError("Attempt to mutate frozen Environment")
        for k, v in iterable:
            self._store[k] = v

    # --- utility ---------------------------------------------------------
    def copy(self, *, frozen: bool | None = None) -> "Environment":
        """Return a *shallow* copy.  Optionally change ``frozen`` flag."""

        return Environment(self._store, frozen=self._frozen if frozen is None else frozen)

    # --- iteration helpers (useful for tests & debugging) ----------------
    def __iter__(self) -> Iterator[Symbol]:
        return iter(self._store)

    def keys(self) -> Iterable[Symbol]:  # noqa: D401 – helper
        return self._store.keys()


# ---------------------------------------------------------------------------
# Utility – standard primitives (fresh copy for each Env).
# ---------------------------------------------------------------------------


def _default_primitives() -> Dict[Symbol, Procedure]:
    return {
        "+": lambda x, y: x + y,
        "*": lambda x, y: x * y,
        "-": lambda x, y: x - y,
        "/": lambda x, y: x / y,
        "=": lambda x, y: x == y,
        "<": lambda x, y: x < y,
        ">": lambda x, y: x > y,
    }


# ---------------------------------------------------------------------------
# Interpreter – now logs evaluative steps at DEBUG level.
# ---------------------------------------------------------------------------


class Interpreter:  # noqa: D101 – docstring below
    """A tiny yet extensible interpreter for *pyscheme* with logging hooks."""

    __slots__ = ("_env", "_dispatch")

    def __init__(self, env: Environment | None = None) -> None:  # noqa: D401 – init
        self._env: Environment = env or Environment(_default_primitives())
        self._dispatch = {
            "define": self._handle_define,
            "if": self._handle_if,
            "lambda": self._handle_lambda,
        }

    # ------------------------------------------------------------------
    # Evaluation entry point
    # ------------------------------------------------------------------

    def evaluate(self, expr: Expression) -> Value | None:  # noqa: C901 – keep flat
        logger.debug("Evaluating %s", expr)

        if isinstance(expr, (int, float)):
            return expr  # type: ignore[return-value]
        if callable(expr):
            return expr  # type: ignore[return-value]
        if isinstance(expr, str):
            value = self._env[expr]  # may raise UndefinedSymbolError
            logger.debug("Symbol %s => %s", expr, value)
            return value  # type: ignore[return-value]
        if not isinstance(expr, tuple):  # type: ignore[unreachable]
            raise InvalidExpressionError(f"Unsupported expression: {expr!r}")

        head, *tail = expr

        # Special forms
        if head in self._dispatch:
            result = self._dispatch[head](tail)  # type: ignore[arg-type]
            logger.debug("Special‑form %s => %s", head, result)
            return result

        # Procedure application
        procedure = self.evaluate(head)
        if not callable(procedure):  # pragma: no cover
            raise InvalidExpressionError(f"Attempted to call non‑callable: {procedure!r}")
        args: Iterable[Value] = (self.evaluate(arg) for arg in tail)
        result = procedure(*args)  # type: ignore[arg-type]
        logger.debug("Application %s %s => %s", head, tail, result)
        return result

    # ------------------------------------------------------------------
    # Special‑form handlers
    # ------------------------------------------------------------------

    def _handle_define(self, args: list[Expression]) -> None:
        if len(args) != 2 or not isinstance(args[0], str):
            raise InvalidExpressionError("Malformed define; expected ('define', <symbol>, <expr>)")
        symbol, value_expr = args
        self._env[symbol] = self.evaluate(value_expr)  # type: ignore[assignment]
        logger.debug("Defined %s", symbol)
        return None

    def _handle_if(self, args: list[Expression]) -> Value:
        if len(args) != 3:
            raise InvalidExpressionError("Malformed if; expected ('if', <cond>, <then>, <else>)")
        cond_expr, then_expr, else_expr = args
        branch = then_expr if self.evaluate(cond_expr) else else_expr
        return self.evaluate(branch)

    def _handle_lambda(self, args: list[Expression]) -> Procedure:
        if len(args) != 2 or not isinstance(args[0], tuple):
            raise InvalidExpressionError("Malformed lambda; expected ('lambda', (<params>,), <body>)")
        param_names: Tuple[Symbol, ...] = args[0]  # type: ignore[assignment]
        body_expr: Expression = args[1]  # type: ignore[assignment]

        env_snapshot = self._env.copy(frozen=True)

        def _procedure(*values: Value) -> Value:  # noqa: D401 – closure
            if len(values) != len(param_names):
                raise EvaluationError(f"Expected {len(param_names)} args but got {len(values)}")
            nested = Interpreter(env_snapshot.copy())
            nested._env.update(zip(param_names, values))  # type: ignore[arg-type]
            return nested.evaluate(body_expr)

        logger.debug("Created lambda with params %s", param_names)
        return _procedure

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def register(self, name: Symbol, proc: Procedure) -> None:  # noqa: D401 – imperative
        """Add/replace a primitive or procedure."""

        self._env[name] = proc  # type: ignore[assignment]
        logger.debug("Registered custom primitive %s", name)

    # Make the interpreter callable
    def __call__(self, expr: Expression) -> Value | None:  # noqa: D401 – dunder
        return self.evaluate(expr)


# ---------------------------------------------------------------------------
# Global façade – backward compatibility
# ---------------------------------------------------------------------------

def _global_interpreter() -> Interpreter:  # noqa: D401 – helper
    if not hasattr(_global_interpreter, "instance"):
        _global_interpreter.instance = Interpreter()  # type: ignore[attr-defined]
    return _global_interpreter.instance  # type: ignore[return-value]


def evaluate(expr: Expression) -> Value | None:  # noqa: D401 – public façade
    """Evaluate *expr* via the module‑level interpreter (backwards‑compat)."""

    return _global_interpreter().evaluate(expr)
