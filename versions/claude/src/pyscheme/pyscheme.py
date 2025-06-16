definitions = {
    "+": lambda x, y: x + y,
    "*": lambda x, y: x * y,
    "-": lambda x, y: x - y,
    "/": lambda x, y: x / y,
    "=": lambda x, y: x == y,
    "<": lambda x, y: x < y,
    ">": lambda x, y: x > y,
}


def evaluate(expression):
    # For primitives, return as is.
    if isinstance(expression, int) or callable(expression):
        return expression

    # For symbols, do a look-up.
    elif isinstance(expression, str):
        return definitions[expression]

    # For tuples, separate special forms vs application of procedures.
    elif isinstance(expression, tuple):
        if expression[0] == "define":
            definitions[expression[1]] = evaluate(expression[2])
            return None

        elif expression[0] == "if":
            if evaluate(expression[1]):
                return evaluate(expression[2])

            return evaluate(expression[3])

        elif expression[0] == "lambda":

            def substitute(expr, name, value):
                if expr == name:
                    return value

                elif isinstance(expr, tuple):
                    return tuple([substitute(term, name, value) for term in expr])

                return expr

            def procedure(*arguments):
                names = expression[1]
                body = expression[2]

                for i, argument in enumerate(arguments):
                    name = names[i]
                    body = substitute(body, name, argument)

                return evaluate(body)

            return procedure

        # Look up procedure and apply to evaluated arguments.
        proc = evaluate(expression[0])
        args = [evaluate(expr) for expr in expression[1:]]

        return proc(*args)
