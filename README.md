# mcp-z3-prover

> MCP server exposing Z3 solver API

[![PyPI](https://img.shields.io/pypi/v/mcp-z3-prover.svg)](https://pypi.org/project/mcp-z3-prover/)
[![Python](https://img.shields.io/pypi/pyversions/mcp-z3-prover.svg)](https://pypi.org/project/mcp-z3-prover/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

## Install

```bash
pip install mcp-z3-prover
```

## Usage

```python
from mcp_z3_prover import mcp

# Run the server
mcp.run()
```

Or from command line:

```bash
mcp-z3-prover
```

## MCP Tools

The server exposes the following tools:

- **create_bool_var** - Create a Boolean variable
- **create_int_var** - Create an Integer variable
- **create_real_var** - Create a Real variable
- **create_int_constant** - Create an integer constant
- **create_real_constant** - Create a real constant
- **add_constraint** - Add a constraint to the solver
- **solve** - Solve the current problem
- **get_model_value** - Get value of a variable from the model
- **optimize** - Solve with optimization objective
- **reset_solver** - Reset the solver state
- **list_variables** - List all created variables

## Example

```python
# Create variables
create_int_var("x")
create_int_var("y")

# Add constraints
add_constraint("int:x + int:y == 10")
add_constraint("int:x > 0")
add_constraint("int:y > 0")

# Solve
result = solve()
# Returns: {"status": "sat", "model": {"x": "5", "y": "5"}}

# Get specific values
x_val = get_model_value("int:x")
```

### Integer Factorization Example

```python
# Factor n = 4295229443 where n = p * q with q <= sqrt(n)
create_int_var("p")
create_int_var("q")

# Add constraints
add_constraint("int:p * int:q == 4295229443")
add_constraint("4295229443 > int:p")
add_constraint("4295229443 > int:q")
add_constraint("int:q <= 65537")  # sqrt(4295229443) ≈ 65537
add_constraint("int:q > 1")
add_constraint("int:p > 1")
add_constraint("int:q % 2 != 0")  # q is odd
add_constraint("int:p % 2 != 0")  # p is odd

# Solve
result = solve()
# Returns: {"status": "sat", "model": {"p": "65539", "q": "65537"}}
# Verification: 65537 * 65539 = 4295229443
```

## Development

```bash
git clone https://github.com/daedalus/mcp-z3-prover.git
cd mcp-z3-prover
pip install -e ".[test]"

# run tests
pytest

# format
ruff format src/ tests/

# lint
ruff check src/ tests/

# type check
mypy src/
```

## MCP Registration

mcp-name: io.github.daedalus/mcp-z3-prover
