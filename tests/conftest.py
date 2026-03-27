import pytest


@pytest.fixture
def clean_session():
    """Fixture to reset the Z3 session before each test."""
    from mcp_z3_prover._core import reset_solver

    reset_solver()
    yield
    reset_solver()


@pytest.fixture
def sample_bool_var(clean_session):
    """Fixture that creates a sample Boolean variable."""
    from mcp_z3_prover._core import create_bool_var

    return create_bool_var("x")


@pytest.fixture
def sample_int_var(clean_session):
    """Fixture that creates a sample Integer variable."""
    from mcp_z3_prover._core import create_int_var

    return create_int_var("y")


@pytest.fixture
def sample_real_var(clean_session):
    """Fixture that creates a sample Real variable."""
    from mcp_z3_prover._core import create_real_var

    return create_real_var("z")
