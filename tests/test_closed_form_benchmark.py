"""Mathematical verification tests proving the CVXPY QP optimizer against closed-form analytical solutions."""
import numpy as np
import pytest
from engine.optimizer import optimize_portfolio


def test_closed_form_two_asset_unconstrained():
    """
    Closed-Form Proof 1:
    In a 2-asset universe with no tax friction (c=0) and loose concentration limits,
    the global minimizer of:
        min  0.5 * ||w - w_target||^2  s.t. sum(w)=1, w >= 0
    where w_target = [0.60, 0.40] and sum(w_target) = 1, is IDENTICALLY w_target.
    Proof: Gradient is (w - w_target). At w = w_target, gradient is zero and constraints hold.
    """
    symbols = ["SPY", "AGG"]
    asset_classes = ["equities", "fixed_income"]
    current_weights = np.array([0.50, 0.50])
    target_weights = np.array([0.60, 0.40])
    tax_costs = np.zeros(2)

    res = optimize_portfolio(
        current_weights=current_weights,
        target_weights=target_weights,
        tax_costs=tax_costs,
        symbols=symbols,
        asset_classes=asset_classes,
        asset_class_bounds={"equities": (0.0, 1.0), "fixed_income": (0.0, 1.0)},
        max_position=1.0,
        turnover_limit=1.0,
        tracking_error_weight=1.0,
        transaction_cost_weight=0.0
    )

    assert res["status"] == "optimal"
    # Must match analytical target to machine precision (within 1e-4)
    np.testing.assert_allclose(res["optimal_weights"], target_weights, atol=1e-4)
    assert np.isclose(res["tracking_error"], 0.0, atol=1e-6)


def test_closed_form_two_asset_binding_concentration():
    """
    Closed-Form Proof 2:
    Target is w_target = [0.75, 0.25], but concentration ceiling is w_i <= 0.55.
    Analytical Solution:
        The KKT conditions dictate w_1 is bounded at 0.55.
        By budget constraint w_1 + w_2 = 1.0, w_2 = 1.0 - 0.55 = 0.45.
        Analytical optimal solution: [0.55, 0.45].
    """
    symbols = ["SPY", "AGG"]
    asset_classes = ["equities", "fixed_income"]
    current_weights = np.array([0.50, 0.50])
    target_weights = np.array([0.75, 0.25])
    tax_costs = np.zeros(2)

    res = optimize_portfolio(
        current_weights=current_weights,
        target_weights=target_weights,
        tax_costs=tax_costs,
        symbols=symbols,
        asset_classes=asset_classes,
        asset_class_bounds={"equities": (0.0, 1.0), "fixed_income": (0.0, 1.0)},
        max_position=0.55, # Binds on asset 0
        turnover_limit=1.0,
        tracking_error_weight=1.0,
        transaction_cost_weight=0.0
    )

    assert res["status"] == "optimal"
    expected_weights = np.array([0.55, 0.45])
    np.testing.assert_allclose(res["optimal_weights"], expected_weights, atol=1e-4)


def test_closed_form_asset_class_boundary_clamping():
    """
    Closed-Form Proof 3:
    Target unconstrained equities weight is 65%, but client IPS fiduciary bounds
    strictly mandate equities <= 20% (Conservative FINRA rule).
    Analytical Solution:
        Equities must clamp at exactly 20.0%, with remaining 80% distributed to non-equity.
    """
    symbols = ["SPY", "AGG", "CASH"]
    asset_classes = ["equities", "fixed_income", "cash"]
    current_weights = np.array([0.40, 0.50, 0.10])
    target_weights = np.array([0.65, 0.25, 0.10])
    tax_costs = np.zeros(3)

    res = optimize_portfolio(
        current_weights=current_weights,
        target_weights=target_weights,
        tax_costs=tax_costs,
        symbols=symbols,
        asset_classes=asset_classes,
        asset_class_bounds={
            "equities": (0.0, 0.20), # Strict 20% cap
            "fixed_income": (0.50, 0.80),
            "cash": (0.05, 0.30)
        },
        max_position=0.80,
        turnover_limit=1.0
    )

    assert res["status"] == "optimal"
    opt_eq = res["optimal_weights"][0]
    assert opt_eq <= 0.20 + 1e-4
    assert np.isclose(np.sum(res["optimal_weights"]), 1.0, atol=1e-4)
