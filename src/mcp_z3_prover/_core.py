from dataclasses import dataclass, field
from typing import Any, Dict

from fastmcp import FastMCP
from z3 import (
    Bool,
    Int,
    IntVal,
    Optimize,
    Real,
    RealVal,
    Solver,
    sat,
    unsat,
)

mcp = FastMCP(name="mcp-z3-prover")


@dataclass
class Z3Session:
    """A session container for Z3 solver state.

    Attributes:
        solver: The Z3 solver instance for checking satisfiability.
        optimizer: The Z3 optimizer instance for optimization problems.
        variables: Dictionary mapping variable names to Z3 expressions.
        constants: Dictionary mapping constant names to Z3 constant values.
        model: The solution model after solving.
        solved: Whether the solver has been called successfully.
    """

    solver: Solver = field(default_factory=Solver)
    optimizer: Optimize | None = None
    variables: dict[str, Any] = field(default_factory=dict)
    constants: dict[str, Any] = field(default_factory=dict)
    model: Any = None
    solved: bool = False


session = Z3Session()


def parse_expression(expr: str) -> Any:
    import re
    expr = expr.strip()
    expr = expr.strip()

    short_to_full = {}
    for var_ref in session.variables.keys():
        if ":" in var_ref:
            short_name = var_ref.split(":", 1)[1]
            short_to_full[short_name] = var_ref
            short_to_full[var_ref] = var_ref

    def replace_var(match):
        var_name = match.group(0)
        if var_name in short_to_full:
            full_ref = short_to_full[var_name]
            return f"_var_map['{full_ref}']"
        return match.group(0)

    pattern = r"\b(?:bool|int|real):\w+|\b\w+\b"
    expr = re.sub(pattern, replace_var, expr)

    for const_ref, const in session.constants.items():
        if const_ref in expr:
            expr = expr.replace(const_ref, f"_const_map['{const_ref}']")

    local_vars = {"_var_map": session.variables, "_const_map": session.constants}
    result = eval(expr, {"__builtins__": {}}, local_vars)
    return result


@mcp.tool
def create_bool_var(name: str) -> str:
    """Create a Boolean variable with the given name.

    Args:
        name: The name of the boolean variable to create.

    Returns:
        The variable reference string in the format 'bool:<name>'.

    Raises:
        ValueError: If a variable with the given name already exists.

    Example:
        >>> create_bool_var("x")
        'bool:x'
    """
    var_name = f"bool:{name}"
    if var_name in session.variables:
        raise ValueError(f"Variable {name} already exists")
    session.variables[var_name] = Bool(name)
    return var_name


@mcp.tool
def create_int_var(name: str) -> str:
    """Create an Integer variable with the given name.

    Args:
        name: The name of the integer variable to create.

    Returns:
        The variable reference string in the format 'int:<name>'.

    Raises:
        ValueError: If a variable with the given name already exists.

    Example:
        >>> create_int_var("n")
        'int:n'
    """
    var_name = f"int:{name}"
    if var_name in session.variables:
        raise ValueError(f"Variable {name} already exists")
    session.variables[var_name] = Int(name)
    return var_name


@mcp.tool
def create_real_var(name: str) -> str:
    """Create a Real (floating-point) variable with the given name.

    Args:
        name: The name of the real variable to create.

    Returns:
        The variable reference string in the format 'real:<name>'.

    Raises:
        ValueError: If a variable with the given name already exists.

    Example:
        >>> create_real_var("x")
        'real:x'
    """
    var_name = f"real:{name}"
    if var_name in session.variables:
        raise ValueError(f"Variable {name} already exists")
    session.variables[var_name] = Real(name)
    return var_name


@mcp.tool
def create_int_constant(value: int) -> str:
    """Create an integer constant with the given value.

    Args:
        value: The integer value for the constant.

    Returns:
        The constant reference string in the format 'int:<value>'.

    Example:
        >>> create_int_constant(42)
        'int:42'
    """
    const_name = f"int:{value}"
    if const_name not in session.constants:
        session.constants[const_name] = IntVal(value)
    return const_name


@mcp.tool
def create_real_constant(value: float) -> str:
    """Create a real constant with the given value.

    Args:
        value: The real value for the constant.

    Returns:
        The constant reference string in the format 'real:<value>'.

    Example:
        >>> create_real_constant(3.14)
        'real:3.14'
    """
    const_name = f"real:{value}"
    if const_name not in session.constants:
        session.constants[const_name] = RealVal(value)
    return const_name


@mcp.tool
def add_constraint(constraint: str) -> dict[str, str]:
    """Add a constraint to the solver.

    Use variable references like 'bool:x', 'int:y', 'real:z' in expressions.
    Supports standard Z3 Python API syntax.

    Args:
        constraint: A Z3 constraint expression as a string.

    Returns:
        A dictionary with status and the constraint that was added.

    Raises:
        ValueError: If the constraint cannot be parsed.

    Example:
        >>> create_int_var("x")
        'int:x'
        >>> create_int_var("y")
        'int:y'
        >>> add_constraint("int:x + int:y > 10")
        {'status': 'success', 'constraint': 'int:x + int:y > 10'}
    """
    try:
        z3_constraint = parse_expression(constraint)
        session.solver.add(z3_constraint)
        return {"status": "success", "constraint": constraint}
    except Exception as e:
        raise ValueError(f"Failed to parse constraint: {e}")


@mcp.tool
def solve(timeout_ms: int = 30000) -> dict[str, Any]:
    """Solve the current problem and return the result.

    Checks all added constraints for satisfiability and returns
    a model if the problem is SAT.

    Args:
        timeout_ms: Timeout in milliseconds for the solver.

    Returns:
        A dictionary containing:
        - status: 'sat', 'unsat', or 'unknown'
        - model: (if sat) A dictionary of variable assignments
        - message: (if unsat/unknown) A description of the result
    """
    session.solver.set("timeout", timeout_ms)
    result = session.solver.check()
    session.solved = True

    if result == sat:
        session.model = session.solver.model()
        return {
            "status": "sat",
            "model": {str(k): str(session.model[k]) for k in session.model},
        }
    elif result == unsat:
        return {"status": "unsat", "message": "Problem is unsatisfiable"}
    else:
        return {
            "status": "unknown",
            "message": "Solver could not determine satisfiability",
        }


@mcp.tool
def get_model_value(variable: str) -> str:
    """Get the value of a variable from the model after solving.

    Args:
        variable: The variable reference (e.g., 'int:x', 'bool:y').

    Returns:
        The value of the variable as a string.

    Raises:
        RuntimeError: If solve() has not been called yet.
        ValueError: If the variable is not known.

    Example:
        >>> create_int_var("x")
        'int:x'
        >>> add_constraint("int:x == 42")
        {'status': 'success', 'constraint': 'int:x == 42'}
        >>> solve()
        {'status': 'sat', 'model': {'x': '42'}}
        >>> get_model_value("int:x")
        '42'
    """
    if not session.solved or session.model is None:
        raise RuntimeError("No model available. Call solve() first.")

    if variable not in session.variables:
        raise ValueError(f"Unknown variable: {variable}")

    var = session.variables[variable]
    val = session.model[var]
    return str(val)


@mcp.tool
def optimize(objective: str, maximize: bool = True, timeout_ms: int = 30000) -> dict[str, Any]:
    """Solve with an optimization objective (maximize or minimize).

    Finds the optimal value for the given objective function subject
    to all added constraints.

    Args:
        objective: The expression to optimize (e.g., 'int:x + int:y').
        maximize: If True, maximize the objective; if False, minimize.
        timeout_ms: Timeout in milliseconds for the optimizer.

    Returns:
        A dictionary containing:
        - status: 'sat', 'unsat', or 'unknown'
        - optimal_value: (if sat) The optimal value of the objective
        - model: (if sat) A dictionary of variable assignments
        - message: (if unsat/unknown) A description of the result
    """
    session.optimizer = Optimize()
    session.optimizer.set("timeout", timeout_ms)

    for constraint in session.solver.assertions():
        session.optimizer.add(constraint)

    z3_objective = parse_expression(objective)

    if maximize:
        h = session.optimizer.maximize(z3_objective)
    else:
        h = session.optimizer.minimize(z3_objective)

    result = session.optimizer.check()
    session.solved = True

    if result == sat:
        session.model = session.optimizer.model()
        opt_value = h.value()
        return {
            "status": "sat",
            "optimal_value": str(opt_value),
            "model": {str(k): str(session.model[k]) for k in session.model},
        }
    elif result == unsat:
        return {"status": "unsat", "message": "Problem is unsatisfiable"}
    else:
        return {
            "status": "unknown",
            "message": "Solver could not determine satisfiability",
        }


@mcp.tool
def reset_solver() -> dict[str, str]:
    """Reset the solver state.

    Clears all variables, constants, constraints, and model data.
    Useful when starting a new problem.

    Returns:
        A dictionary with status and a success message.

    Example:
        >>> create_int_var("x")
        'int:x'
        >>> add_constraint("int:x > 5")
        {'status': 'success', 'constraint': 'int:x > 5'}
        >>> reset_solver()
        {'status': 'success', 'message': 'Solver reset successfully'}
        >>> list_variables()
        {'variables': []}
    """
    session.solver = Solver()
    session.optimizer = None
    session.variables = {}
    session.constants = {}
    session.model = None
    session.solved = False
    return {"status": "success", "message": "Solver reset successfully"}


@mcp.tool
def list_variables() -> dict[str, list[str]]:
    """List all created variables.

    Returns:
        A dictionary containing a list of all variable references.

    Example:
        >>> create_int_var("x")
        'int:x'
        >>> create_bool_var("flag")
        'bool:flag'
        >>> list_variables()
        {'variables': ['int:x', 'bool:flag']}
    """
    return {"variables": list(session.variables.keys())}
