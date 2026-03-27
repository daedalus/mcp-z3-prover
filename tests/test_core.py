import pytest
from mcp_z3_prover import _core


class TestCreateBoolVar:
    """Tests for create_bool_var tool."""

    def test_create_bool_var(self, clean_session):
        result = _core.create_bool_var("x")
        assert result == "bool:x"

    def test_create_duplicate_bool_var(self, clean_session):
        _core.create_bool_var("x")
        with pytest.raises(ValueError, match="already exists"):
            _core.create_bool_var("x")


class TestCreateIntVar:
    """Tests for create_int_var tool."""

    def test_create_int_var(self, clean_session):
        result = _core.create_int_var("y")
        assert result == "int:y"

    def test_create_duplicate_int_var(self, clean_session):
        _core.create_int_var("y")
        with pytest.raises(ValueError, match="already exists"):
            _core.create_int_var("y")


class TestCreateRealVar:
    """Tests for create_real_var tool."""

    def test_create_real_var(self, clean_session):
        result = _core.create_real_var("z")
        assert result == "real:z"

    def test_create_duplicate_real_var(self, clean_session):
        _core.create_real_var("z")
        with pytest.raises(ValueError, match="already exists"):
            _core.create_real_var("z")


class TestCreateConstants:
    """Tests for create_int_constant and create_real_constant tools."""

    def test_create_int_constant(self, clean_session):
        result = _core.create_int_constant(5)
        assert result == "int:5"

    def test_create_real_constant(self, clean_session):
        result = _core.create_real_constant(3.14)
        assert "real:3.14" in result


class TestAddConstraint:
    """Tests for add_constraint tool."""

    def test_add_simple_constraint(self, clean_session):
        _core.create_int_var("x")
        _core.create_int_var("y")
        result = _core.add_constraint("int:x + int:y > 5")
        assert result["status"] == "success"

    def test_add_bool_constraint(self, clean_session):
        _core.create_bool_var("a")
        _core.create_bool_var("b")
        result = _core.add_constraint("bool:a == bool:b")
        assert result["status"] == "success"

    def test_add_real_constraint(self, clean_session):
        _core.create_real_var("r")
        result = _core.add_constraint("real:r > 0.5")
        assert result["status"] == "success"


class TestSolve:
    """Tests for solve tool."""

    def test_solve_sat(self, clean_session):
        _core.create_int_var("x")
        _core.add_constraint("int:x > 0")
        _core.add_constraint("int:x < 10")
        result = _core.solve()
        assert result["status"] == "sat"
        assert "model" in result

    def test_solve_unsat(self, clean_session):
        _core.create_int_var("x")
        _core.add_constraint("int:x > 5")
        _core.add_constraint("int:x < 5")
        result = _core.solve()
        assert result["status"] == "unsat"

    def test_solve_empty_constraints(self, clean_session):
        _core.create_int_var("x")
        result = _core.solve()
        assert result["status"] == "sat"


class TestGetModelValue:
    """Tests for get_model_value tool."""

    def test_get_model_value_after_solve(self, clean_session):
        _core.create_int_var("x")
        _core.add_constraint("int:x == 42")
        _core.solve()
        result = _core.get_model_value("int:x")
        assert result == "42"

    def test_get_model_value_without_solve(self, clean_session):
        _core.create_int_var("x")
        with pytest.raises(RuntimeError, match="No model available"):
            _core.get_model_value("int:x")


class TestOptimize:
    """Tests for optimize tool."""

    def test_maximize(self, clean_session):
        _core.create_int_var("x")
        _core.add_constraint("int:x >= 0")
        _core.add_constraint("int:x <= 10")
        result = _core.optimize("int:x", maximize=True)
        assert result["status"] == "sat"
        assert result["optimal_value"] == "10"

    def test_minimize(self, clean_session):
        _core.create_int_var("y")
        _core.add_constraint("int:y >= 0")
        _core.add_constraint("int:y <= 10")
        result = _core.optimize("int:y", maximize=False)
        assert result["status"] == "sat"
        assert result["optimal_value"] == "0"


class TestResetSolver:
    """Tests for reset_solver tool."""

    def test_reset_solver(self, clean_session):
        _core.create_int_var("x")
        _core.add_constraint("int:x > 0")
        result = _core.reset_solver()
        assert result["status"] == "success"
        assert len(_core.session.variables) == 0


class TestListVariables:
    """Tests for list_variables tool."""

    def test_list_empty_variables(self, clean_session):
        result = _core.list_variables()
        assert result["variables"] == []

    def test_list_variables(self, clean_session):
        _core.create_int_var("x")
        _core.create_bool_var("y")
        result = _core.list_variables()
        assert "int:x" in result["variables"]
        assert "bool:y" in result["variables"]
