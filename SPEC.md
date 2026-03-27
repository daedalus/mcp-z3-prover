# SPEC.md — mcp-z3-prover

## Purpose

An MCP (Model Context Protocol) server that exposes the Z3 theorem prover/solver API. It provides an easy-to-use interface for defining and solving satisfiability (SAT), optimization, and constraint satisfaction problems using Z3.

## Scope

### In Scope
- MCP server implementation using FastMCP
- Tools for defining variables (Boolean, Integer, Real)
- Tools for creating constraints/expressions
- Tools for solving problems and retrieving models
- Support for optimization (maximize/minimize)
- STDIO transport for MCP communication

### Not in Scope
- Interactive theorem proving workflows
- Proof generation or certificate extraction
- SMT-LIB file parsing/serialization
- Integration with other solvers beyond Z3

## Public API

### MCP Tools

1. **`create_bool_var`** - Create a Boolean variable
   - Args: `name` (str): Variable name
   - Returns: Variable reference string

2. **`create_int_var`** - Create an Integer variable
   - Args: `name` (str): Variable name
   - Returns: Variable reference string

3. **`create_real_var`** - Create a Real variable
   - Args: `name` (str): Variable name
   - Returns: Variable reference string

4. **`create_int_constant`** - Create an integer constant
   - Args: `value` (int): Integer value
   - Returns: Constant reference string

5. **`create_real_constant`** - Create a real constant
   - Args: `value` (float): Real value
   - Returns: Constant reference string

6. **`add_constraint`** - Add a constraint to the solver
   - Args:
     - `constraint` (str): Constraint expression (e.g., "x + y > 5")
     - `name` (str, optional): Optional name for the constraint
   - Returns: Success status

7. **`solve`** - Solve the current problem
   - Args: None
   - Returns: Solution status ("sat", "unsat", "unknown") and model if sat

8. **`get_model_value`** - Get value of a variable from the model
   - Args: `variable` (str): Variable reference
   - Returns: Value as string

9. **`optimize`** - Solve with optimization objective
   - Args:
     - `objective` (str): Expression to maximize/minimize
     - `maximize` (bool): True to maximize, False to minimize
   - Returns: Optimal value and model

10. **`reset_solver`** - Reset the solver state
    - Args: None
    - Returns: Success status

### Session State
The server maintains session state for:
- Created variables (Bool, Int, Real)
- Added constraints
- Current model (after solve)

## Data Formats

### Input/Output
- All expressions passed as strings (e.g., "x + y >= 10")
- Variable references as strings (e.g., "bool:x", "int:y", "real:z")
- Results returned as JSON-serializable dictionaries

### Error Messages
- Clear error messages for invalid expressions
- Clear error messages for unsatisfiable problems

## Edge Cases

1. **Duplicate variable names** - Should raise an error
2. **Unknown variable in expression** - Should raise an error
3. **Unsatisfiable problem** - Should return "unsat" with helpful message
4. **Optimize without constraints** - Should work (single variable optimization)
5. **Get model without solving** - Should raise an error
6. **Invalid expression syntax** - Should raise a parse error
7. **Empty constraint list** - SAT trivially (any model works)
8. **Real arithmetic precision** - Handle floating-point appropriately

## Performance & Constraints

- Single-threaded solver per session
- No timeout by default (relies on Z3 defaults)
- Memory usage bounded by Z3 constraints
- Target Python 3.11+
