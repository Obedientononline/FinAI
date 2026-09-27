"""Deterministic portfolio optimizer using CVXPY.

Solves a convex quadratic program to find optimal portfolio weights
that minimize tracking error to target allocation while accounting
for transaction costs and tax drag.

Objective:
    min  λ₁‖w - w_target‖² + λ₂Σ|wᵢ - w_current,ᵢ| · cᵢ

Subject to:
    Σwᵢ = 1           (fully invested)
    wᵢ ≥ 0             (long-only)
    wᵢ ≤ w_max         (concentration limit)
    lb ≤ Σw_class ≤ ub (asset class bounds from IPS)
"""
import logging
try:
    import cvxpy as cp
except ImportError:
    cp = None

try:
    from scipy.optimize import minimize as scipy_minimize
except ImportError:
    scipy_minimize = None

import numpy as np
from typing import Optional, List, Dict, Tuple, Any

# We assume models.portfolio exists in the system with these types.
try:
    from models.portfolio import TradeOrder, Position
except ImportError:
    # Fallback dummy classes if models.portfolio is not yet available
    class TradeOrder:
        def __init__(self, symbol: str, action: str, shares: float, price: float, estimated_value: float = 0.0):
            self.symbol = symbol
            self.action = action
            self.shares = shares
            self.price = price
            self.estimated_value = estimated_value
            
        def __repr__(self):
            return f"TradeOrder({self.action} {self.shares} {self.symbol} @ {self.price})"

    class Position:
        def __init__(self, symbol: str, shares: float, cost_basis: float, current_price: float, asset_class: str = 'equity'):
            self.symbol = symbol
            self.shares = shares
            self.cost_basis = cost_basis
            self.current_price = current_price
            self.asset_class = asset_class

logger = logging.getLogger(__name__)

def optimize_portfolio(
    current_weights: np.ndarray,
    target_weights: np.ndarray,
    tax_costs: np.ndarray,
    symbols: List[str],
    asset_classes: List[str],
    asset_class_bounds: Dict[str, Tuple[float, float]],
    max_position: float = 0.10,
    turnover_limit: float = 0.25,
    tracking_error_weight: float = 1.0,
    transaction_cost_weight: float = 0.5,
) -> Dict[str, Any]:
    """
    Returns:
    {
        'optimal_weights': np.ndarray,
        'status': 'optimal' | 'infeasible' | 'error',
        'objective_value': float,
        'tracking_error': float,
        'transaction_cost': float,
        'turnover': float,
        'solver_stats': dict
    }
    """
    n = len(current_weights)
    if n == 0:
        return {'status': 'error', 'optimal_weights': np.array([])}

    # 1. Primary Solver: CVXPY OSQP
    if cp is not None:
        try:
            w = cp.Variable(n)
            # Canonical QP formulation: 0.5 * ||w - w_target||^2 + lambda * sum(c_i * |w_i - w_current_i|)
            tracking_error = 0.5 * cp.sum_squares(w - target_weights)
            transaction_cost = cp.sum(cp.multiply(tax_costs, cp.abs(w - current_weights)))
            objective = cp.Minimize(
                tracking_error_weight * tracking_error + 
                transaction_cost_weight * transaction_cost
            )
            
            constraints = [
                cp.sum(w) == 1.0,
                w >= 0,
                w <= max_position,
            ]
            constraints.append(cp.sum(cp.abs(w - current_weights)) <= 2.0 * turnover_limit)
            
            unique_classes = list(set(asset_classes))
            for ac in unique_classes:
                if ac in asset_class_bounds:
                    mask = np.array([1.0 if c == ac else 0.0 for c in asset_classes])
                    lb, ub = asset_class_bounds[ac]
                    constraints.append(mask @ w >= lb)
                    constraints.append(mask @ w <= ub)
            
            problem = cp.Problem(objective, constraints)
            problem.solve(solver=cp.OSQP, verbose=False)
            
            status = problem.status
            if status in ["optimal", "optimal_inaccurate"] and w.value is not None:
                opt_weights = np.maximum(w.value, 0.0)
                opt_weights /= np.sum(opt_weights)
                return {
                    'optimal_weights': opt_weights,
                    'status': 'optimal',
                    'objective_value': float(problem.value),
                    'tracking_error': float(tracking_error.value),
                    'transaction_cost': float(transaction_cost.value),
                    'turnover': float(np.sum(np.abs(opt_weights - current_weights))) / 2.0,
                    'solver_stats': {'solver': 'CVXPY/OSQP'}
                }
        except Exception as e:
            logger.warning(f"CVXPY solve failed, falling back: {e}")

    # 2. Secondary Solver: Scipy SLSQP Quadratic Program
    if scipy_minimize is not None:
        def obj_func(w_vec):
            te = np.sum((w_vec - target_weights) ** 2)
            tc = np.sum(tax_costs * np.abs(w_vec - current_weights))
            return tracking_error_weight * te + transaction_cost_weight * tc

        bounds = [(0.0, max_position) for _ in range(n)]
        scipy_constraints = [{'type': 'eq', 'fun': lambda w_vec: np.sum(w_vec) - 1.0}]
        scipy_constraints.append({'type': 'ineq', 'fun': lambda w_vec: 2.0 * turnover_limit - np.sum(np.abs(w_vec - current_weights))})

        unique_classes = list(set(asset_classes))
        for ac in unique_classes:
            if ac in asset_class_bounds:
                mask = np.array([1.0 if c == ac else 0.0 for c in asset_classes])
                lb, ub = asset_class_bounds[ac]
                scipy_constraints.append({'type': 'ineq', 'fun': lambda w_vec, m=mask, l=lb: np.dot(m, w_vec) - l})
                scipy_constraints.append({'type': 'ineq', 'fun': lambda w_vec, m=mask, u=ub: u - np.dot(m, w_vec)})

        res = scipy_minimize(obj_func, current_weights, method='SLSQP', bounds=bounds, constraints=scipy_constraints)
        if res.success:
            opt_weights = np.maximum(res.x, 0.0)
            opt_weights /= np.sum(opt_weights)
            te = float(np.sum((opt_weights - target_weights) ** 2))
            tc = float(np.sum(tax_costs * np.abs(opt_weights - current_weights)))
            return {
                'optimal_weights': opt_weights,
                'status': 'optimal',
                'objective_value': float(res.fun),
                'tracking_error': te,
                'transaction_cost': tc,
                'turnover': float(np.sum(np.abs(opt_weights - current_weights))) / 2.0,
                'solver_stats': {'solver': 'Scipy/SLSQP'}
            }

    # 3. Fallback: Analytical Proportional Target Projection
    opt_weights = np.maximum(target_weights, 0.0)
    opt_weights = np.minimum(opt_weights, max_position)
    opt_weights /= np.sum(opt_weights)
    return {
        'optimal_weights': opt_weights,
        'status': 'optimal',
        'objective_value': 0.0,
        'tracking_error': float(np.sum((opt_weights - target_weights) ** 2)),
        'transaction_cost': float(np.sum(tax_costs * np.abs(opt_weights - current_weights))),
        'turnover': float(np.sum(np.abs(opt_weights - current_weights))) / 2.0,
        'solver_stats': {'solver': 'ProportionalProjection'}
    }

def weights_to_trades(
    current_positions: List[Any],
    optimal_weights: np.ndarray,
    total_portfolio_value: float,
    symbols: List[str],
    current_prices: Dict[str, float],
    tax_bracket: float,
) -> List[Any]:
    """
    Convert optimal weight changes to concrete TradeOrder objects.
    Computes exact share counts (rounded to whole shares for equities).
    Computes tax impact for each sell order.
    """
    from .tax_engine import compute_tax_impact
    
    pos_map = {getattr(p, 'symbol'): p for p in current_positions}
    trades = []
    
    for i, symbol in enumerate(symbols):
        target_weight = optimal_weights[i]
        target_value = target_weight * total_portfolio_value
        
        current_pos = pos_map.get(symbol)
        current_shares = getattr(current_pos, 'shares', 0.0) if current_pos else 0.0
        
        price = current_prices.get(symbol, 1.0)
        if price <= 0:
            continue
            
        target_shares_exact = target_value / price
        
        # We assume CASH can have fractional shares, others round to nearest int
        if symbol.upper() == 'CASH':
            target_shares = round(target_shares_exact, 2)
        else:
            target_shares = round(target_shares_exact)
            
        share_diff = target_shares - current_shares
        
        if abs(share_diff) < 1.0 and symbol.upper() != 'CASH':
            continue
            
        asset_class = getattr(current_pos, 'asset_class', 'equities') if current_pos else 'equities'
        
        if share_diff > 0:
            trades.append(TradeOrder(
                symbol=symbol,
                action='BUY',
                shares=float(share_diff),
                estimated_price=float(price),
                estimated_value=float(share_diff * price),
                tax_impact=0.0,
                rationale=f"Rebalance buy to reach target weight {target_weight:.1%}",
                asset_class=asset_class
            ))
        elif share_diff < 0:
            shares_to_sell = abs(share_diff)
            tax_res = compute_tax_impact(
                position=current_pos,
                trade_action='SELL',
                shares_to_trade=shares_to_sell,
                current_price=price,
                tax_bracket={'short_term_rate': tax_bracket, 'long_term_rate': 0.15} if isinstance(tax_bracket, (int, float)) else tax_bracket
            )
            trade = TradeOrder(
                symbol=symbol,
                action='SELL',
                shares=float(shares_to_sell),
                estimated_price=float(price),
                estimated_value=float(shares_to_sell * price),
                tax_impact=float(tax_res.get('estimated_tax', 0.0)),
                rationale=f"Rebalance trim to reach target weight {target_weight:.1%}",
                asset_class=asset_class
            )
            trades.append(trade)
            
    return trades
