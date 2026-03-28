from dataclasses import dataclass, field
from typing import Any

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
    solver: Solver = field(default_factory=Solver)
    optimizer: Optimize | None = None
    variables: dict[str, Any] = field(default_factory=dict)
    constants: dict[str, Any] = field(default_factory=dict)
    model: Any = None
    solved: bool = False


session = Z3Session()


def parse_expression(expr: str) -> Any:
    """Parse a string expression into a Z3 expression."""
    expr = expr.strip()

    for var_ref, var in session.variables.items():
        if var_ref in expr:
            expr = expr.replace(var_ref, f"_var_map['{var_ref}']")

    for const_ref, const in session.constants.items():
        if const_ref in expr:
            expr = expr.replace(const_ref, f"_const_map['{const_ref}']")

    local_vars = {"_var_map": session.variables, "_const_map": session.constants}
    result = eval(expr, {"__builtins__": {}}, local_vars)
    return result


@mcp.tool
def create_bool_var(name: str) -> str:
    """Create a Boolean variable with the given name."""
    var_name = f"bool:{name}"
    if var_name in session.variables:
        raise ValueError(f"Variable {name} already exists")
    session.variables[var_name] = Bool(name)
    return var_name


@mcp.tool
def create_int_var(name: str) -> str:
    """Create an Integer variable with the given name."""
    var_name = f"int:{name}"
    if var_name in session.variables:
        raise ValueError(f"Variable {name} already exists")
    session.variables[var_name] = Int(name)
    return var_name


@mcp.tool
def create_real_var(name: str) -> str:
    """Create a Real variable with the given name."""
    var_name = f"real:{name}"
    if var_name in session.variables:
        raise ValueError(f"Variable {name} already exists")
    session.variables[var_name] = Real(name)
    return var_name


@mcp.tool
def create_int_constant(value: int) -> str:
    """Create an integer constant with the given value."""
    const_name = f"int:{value}"
    if const_name not in session.constants:
        session.constants[const_name] = IntVal(value)
    return const_name


@mcp.tool
def create_real_constant(value: float) -> str:
    """Create a real constant with the given value."""
    const_name = f"real:{value}"
    if const_name not in session.constants:
        session.constants[const_name] = RealVal(value)
    return const_name


@mcp.tool
def add_constraint(constraint: str) -> dict[str, str]:
    """Add a constraint to the solver. Use variable references like 'bool:x', 'int:y', 'real:z' in expressions."""
    try:
        z3_constraint = parse_expression(constraint)
        session.solver.add(z3_constraint)
        return {"status": "success", "constraint": constraint}
    except Exception as e:
        raise ValueError(f"Failed to parse constraint: {e}")


@mcp.tool
def solve() -> dict[str, Any]:
    """Solve the current problem and return the result."""
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
    """Get the value of a variable from the model after solving."""
    if not session.solved or session.model is None:
        raise RuntimeError("No model available. Call solve() first.")

    if variable not in session.variables:
        raise ValueError(f"Unknown variable: {variable}")

    var = session.variables[variable]
    val = session.model[var]
    return str(val)


@mcp.tool
def optimize(objective: str, maximize: bool = True) -> dict[str, Any]:
    """Solve with optimization objective (maximize or minimize)."""
    session.optimizer = Optimize()

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
    """Reset the solver state (clear all variables, constraints, and model)."""
    session.solver = Solver()
    session.optimizer = None
    session.variables = {}
    session.constants = {}
    session.model = None
    session.solved = False
    return {"status": "success", "message": "Solver reset successfully"}


@mcp.tool
def list_variables() -> dict[str, list[str]]:
    """List all created variables."""
    return {"variables": list(session.variables.keys())}
